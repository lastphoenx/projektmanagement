"""Jira Cloud CSV (Neu-Importer) aus PSP — deterministisch, Phase 5.1."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

from app.services.psp_parse_service import ParsedWorkPackage, parse_psp_work_packages

CSV_COLUMNS = [
    "Work type",
    "Summary",
    "Work item ID",
    "Parent",
    "Description",
    "Priority",
    "Status",
    "Labels",
]

JIRA_CSV_DELIMITER = ";"


@dataclass
class ParsedPhase:
    name: str
    work_packages: list[ParsedWorkPackage] = field(default_factory=list)


def jira_csv_export_filename(project_key: str) -> str:
    key = (project_key or "").strip() or "PROJ"
    return f"{key}_jira_csv.csv"


def group_by_phase(work_packages: list[ParsedWorkPackage]) -> list[ParsedPhase]:
    phases: dict[str, list[ParsedWorkPackage]] = {}
    order: list[str] = []
    for wp in work_packages:
        phase_name = (wp.phase or "Projekt").strip()
        if phase_name not in phases:
            phases[phase_name] = []
            order.append(phase_name)
        phases[phase_name].append(wp)
    return [ParsedPhase(name=name, work_packages=phases[name]) for name in order]


def _safe_id_prefix(project_key: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", (project_key or "").upper())
    return cleaned or "PROJ"


def _extract_project_title(psp_content: str) -> str:
    m = re.search(
        r"###\s*1\.\s*Projekt\s*\n\s*-\s*\*\*(.+?)\*\*",
        psp_content,
        re.IGNORECASE | re.MULTILINE,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r"Projektstrukturplan.*?(?:für|für das Projekt)\s*[«\"']?([^«\"'\n]+)",
        psp_content,
        re.I,
    )
    if m:
        return m.group(1).strip().strip("«»\"'")
    return ""


def _task_description(wp: ParsedWorkPackage) -> str:
    parts = [f"AP-ID: {wp.ap_id}"]
    if wp.responsible:
        parts.append(f"Verantwortlich: {wp.responsible}")
    if wp.effort_pt:
        effort = wp.effort_pt.strip()
        if effort and not re.search(r"\bPT\b", effort, re.I):
            effort = f"{effort} PT"
        parts.append(f"Aufwand: {effort}")
    return " · ".join(parts)


def _epic_summary(project_title: str, phase_name: str) -> str:
    if project_title and phase_name:
        return f"{project_title} – {phase_name}"
    return phase_name or project_title or "Epic"


def build_jira_csv_rows(
    project_key: str,
    psp_content: str,
    project_title: str | None = None,
) -> list[dict[str, str]]:
    work_packages = parse_psp_work_packages(psp_content)
    if not work_packages:
        raise ValueError(
            "Im Projektstrukturplan (PSP) wurden keine Arbeitspakete erkannt. "
            "Bitte PSP mit Tabelle (ID | Bezeichnung | Phase | …) oder AP-Liste pflegen."
        )

    title = (project_title or _extract_project_title(psp_content)).strip()
    prefix = _safe_id_prefix(project_key)
    phases = group_by_phase(work_packages)

    rows: list[dict[str, str]] = []
    counter = 1
    epic_ids: dict[str, str] = {}

    for phase in phases:
        epic_id = f"{prefix}-{counter}"
        counter += 1
        epic_ids[phase.name] = epic_id
        rows.append(
            {
                "Work type": "Epic",
                "Summary": _epic_summary(title, phase.name),
                "Work item ID": epic_id,
                "Parent": "",
                "Description": f"Hauptphase: {phase.name}",
                "Priority": "High",
                "Status": "To Do",
                "Labels": phase.name,
            }
        )

        for wp in phase.work_packages:
            task_id = f"{prefix}-{counter}"
            counter += 1
            task_summary = wp.title.strip()
            if wp.ap_id and wp.ap_id.upper() not in task_summary.upper():
                task_summary = f"{wp.ap_id}: {task_summary}"
            rows.append(
                {
                    "Work type": "Task",
                    "Summary": task_summary,
                    "Work item ID": task_id,
                    "Parent": epic_ids[phase.name],
                    "Description": _task_description(wp),
                    "Priority": "Medium",
                    "Status": "To Do",
                    "Labels": phase.name,
                }
            )

    return rows


def build_jira_csv_from_psp(
    project_key: str,
    psp_content: str,
    project_title: str | None = None,
) -> str:
    rows = build_jira_csv_rows(project_key, psp_content, project_title)
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
        delimiter=JIRA_CSV_DELIMITER,
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().strip()
