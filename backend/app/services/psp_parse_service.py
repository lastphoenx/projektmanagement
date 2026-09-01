"""PSP-Arbeitspakete aus Markdown parsen (Phase 5)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedWorkPackage:
    ap_id: str
    title: str
    phase: str = ""
    responsible: str = ""
    effort_pt: str = ""


_AP_ID_RE = re.compile(r"(?:AP[-\s]*)?(\d+(?:\.\d+)*)", re.I)


def _extract_ap_id(raw: str) -> str | None:
    m = _AP_ID_RE.search(raw.strip())
    if not m:
        return None
    return f"AP{m.group(1)}"


def parse_pt_effort(value: str) -> int:
    if not value:
        return 0
    m = re.search(r"(\d+)", value.replace("'", ""))
    return int(m.group(1)) if m else 0


def parse_psp_work_packages(psp_content: str) -> list[ParsedWorkPackage]:
    if not psp_content or not psp_content.strip():
        return []
    from_table = _parse_table_section(psp_content)
    if from_table:
        return from_table
    return _parse_hierarchy_section(psp_content)


def _parse_table_section(psp_content: str) -> list[ParsedWorkPackage]:
    lines = psp_content.splitlines()
    header_idx: int | None = None
    for i, line in enumerate(lines):
        low = line.lower()
        if "|" in line and ("bezeichnung" in low or "arbeitspaket" in low):
            if any(k in low for k in ("id", "ap", "nr")):
                header_idx = i
                break
    if header_idx is None:
        return []

    header_cells = [c.strip().lower() for c in lines[header_idx].split("|") if c.strip()]

    def col_idx(names: tuple[str, ...]) -> int | None:
        for n in names:
            for idx, h in enumerate(header_cells):
                if n in h:
                    return idx
        return None

    idx_id = col_idx(("ap-id", "id", "ap", "nr"))
    idx_title = col_idx(("bezeichnung", "arbeitspaket", "title", "name"))
    idx_phase = col_idx(("phase", "hauptphase"))
    idx_resp = col_idx(("verantwortlich", "rolle", "responsible"))
    idx_effort = col_idx(("aufwand", "pt", "personentage", "effort"))

    if idx_id is None or idx_title is None:
        return []

    result: list[ParsedWorkPackage] = []
    for line in lines[header_idx + 1 :]:
        if not line.strip().startswith("|") or re.match(r"^\|\s*[-:]+", line):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) <= max(idx_id, idx_title):
            continue
        ap_id = _extract_ap_id(cells[idx_id])
        if not ap_id:
            continue
        result.append(
            ParsedWorkPackage(
                ap_id=ap_id,
                title=cells[idx_title],
                phase=cells[idx_phase] if idx_phase is not None and idx_phase < len(cells) else "",
                responsible=cells[idx_resp] if idx_resp is not None and idx_resp < len(cells) else "",
                effort_pt=cells[idx_effort] if idx_effort is not None and idx_effort < len(cells) else "",
            )
        )
    return result


def _parse_hierarchy_section(psp_content: str) -> list[ParsedWorkPackage]:
    lines = psp_content.splitlines()
    current_phase = ""
    result: list[ParsedWorkPackage] = []
    current: ParsedWorkPackage | None = None
    phase_re = re.compile(r"^#{2,4}\s+(.+?)\s*$")
    ap_re = re.compile(r"^\s*[-*]\s*\*\*(?:AP[-\s]*)?([\d]+(?:\.[\d]+)+)\*\*[:\s]*(.*)$", re.I)
    resp_re = re.compile(r"^\s*[-*]\s*Verantwortlich[:\s]+(.+)$", re.I)
    effort_re = re.compile(r"^\s*[-*]\s*(?:Aufwand|PT)[:\s]+(.+)$", re.I)

    for line in lines:
        pm = phase_re.match(line.strip())
        if pm:
            current_phase = pm.group(1).strip()
            current = None
            continue
        am = ap_re.match(line)
        if am:
            if current:
                result.append(current)
            current = ParsedWorkPackage(
                ap_id=f"AP{am.group(1).strip()}",
                title=am.group(2).strip(),
                phase=current_phase,
            )
            continue
        if current:
            rm = resp_re.match(line)
            if rm:
                current.responsible = rm.group(1).strip()
                continue
            em = effort_re.match(line)
            if em:
                current.effort_pt = em.group(1).strip()
    if current:
        result.append(current)
    return result
