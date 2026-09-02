"""Ressourcenauslastung aus PSP — deterministisch (Phase 6, Einsatzmittelplan-Hybrid)."""

from __future__ import annotations

from app.services.jira_csv_service import group_by_phase
from app.services.psp_parse_service import parse_psp_work_packages, parse_pt_effort


def _fmt_pt(val: float) -> str:
    if val == 0:
        return "0"
    rounded = round(val, 1)
    if abs(rounded - round(rounded)) < 0.05:
        return str(int(round(rounded)))
    return str(rounded)


def build_resource_utilization_table(psp_content: str, *, title: str = "") -> str:
    """Markdown-Tabelle: Rollen- und Phasen-PT aus dem PSP."""
    work_packages = parse_psp_work_packages(psp_content)
    if not work_packages:
        raise ValueError(
            "Im PSP wurden keine Arbeitspakete erkannt. "
            "Bitte zuerst Schritt 3 (PSP) mit PT-Angaben erstellen."
        )

    phases = group_by_phase(work_packages)
    role_total: dict[str, float] = {}
    phase_role_pt: dict[str, dict[str, float]] = {}
    all_roles: list[str] = []
    total_pt = 0.0

    for phase in phases:
        role_pt: dict[str, float] = {}
        for wp in phase.work_packages:
            role = (wp.responsible or "Sonstige").strip()
            pt = float(parse_pt_effort(wp.effort_pt))
            if pt <= 0:
                continue
            role_pt[role] = role_pt.get(role, 0.0) + pt
            role_total[role] = role_total.get(role, 0.0) + pt
            total_pt += pt
            if role not in all_roles:
                all_roles.append(role)
        phase_role_pt[phase.name] = role_pt

    if total_pt <= 0:
        raise ValueError("Keine PT-Werte im PSP gefunden.")

    heading = f"## Ressourcenauslastungsplan – {title}" if title else "## Ressourcenauslastungsplan"
    lines: list[str] = [
        heading,
        "",
        f"> **Basis: PSP (Schritt 3)** — Gesamtaufwand: **{_fmt_pt(total_pt)} PT** "
        f"über {len(all_roles)} Rollen.",
        "",
        "### Rollenübersicht (Gesamt-PT aus PSP)",
        "",
        "| Rolle | Gesamt PT | Anteil |",
        "|-------|-----------|--------|",
    ]
    for role in all_roles:
        pt = role_total[role]
        pct = round(pt / total_pt * 100, 1)
        lines.append(f"| {role} | {_fmt_pt(pt)} | {pct}% |")
    lines.append(f"| **Gesamt** | **{_fmt_pt(total_pt)}** | 100% |")

    lines += ["", "### Personalbedarfsmatrix nach Phase", ""]
    header = ["Phase", *all_roles, "Summe PT"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * len(header)) + " |")

    for phase in phases:
        role_pt = phase_role_pt.get(phase.name, {})
        phase_sum = sum(role_pt.values())
        if phase_sum <= 0:
            continue
        cells = [phase.name]
        cells.extend(_fmt_pt(role_pt.get(role, 0.0)) for role in all_roles)
        cells.append(_fmt_pt(phase_sum))
        lines.append("| " + " | ".join(cells) + " |")

    sum_cells = ["**Total**"]
    sum_cells.extend(f"**{_fmt_pt(role_total[role])}**" for role in all_roles)
    sum_cells.append(f"**{_fmt_pt(total_pt)}**")
    lines.append("| " + " | ".join(sum_cells) + " |")

    return "\n".join(lines)
