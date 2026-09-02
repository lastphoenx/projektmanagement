"""Deterministischer Budgetplan aus PSP (Phase 5.2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.jira_csv_service import group_by_phase
from app.services.project_type_service import rates_for_project_type, role_rate_key
from app.services.psp_parse_service import parse_psp_work_packages, parse_pt_effort


@dataclass
class RoleBudgetLine:
    role: str
    pt: int
    rate_chf: float

    @property
    def total_chf(self) -> float:
        return round(self.pt * self.rate_chf, 2)


@dataclass
class BudgetSkeleton:
    project_title: str
    project_type: str
    role_lines: list[RoleBudgetLine] = field(default_factory=list)
    sachkosten: list[tuple[str, str, float]] = field(default_factory=list)
    phase_costs: list[tuple[str, float]] = field(default_factory=list)
    total_pt: int = 0
    personal_chf: float = 0.0
    sachkosten_chf: float = 0.0
    reserve_chf: float = 0.0
    gesamtbudget: float = 0.0
    skurve: list[int] = field(default_factory=list)
    budget_ceiling_chf: float | None = None


def _format_chf(amount: float) -> str:
    return f"{round(amount):,}".replace(",", "'")


def _format_qty(qty: float | int) -> str:
    return str(max(0, round(float(qty))))


def _default_sachkosten(project_type: str, personal_chf: float) -> list[tuple[str, str, float]]:
    scale = max(1.0, personal_chf / 100_000)
    if project_type == "infrastructure":
        return [
            ("Hardware / Server", "Server und Arbeitsplätze", round(25_000 * scale, 2)),
            ("Infrastruktur und Betrieb", "Hosting, 12 Monate", round(24_000 * scale, 2)),
        ]
    return [
        ("Softwarelizenzen", "Entwicklung und Test", round(15_000 * scale, 2)),
        ("Infrastruktur und Betrieb", "Hosting, 12 Monate", round(24_000 * scale, 2)),
    ]


def _skurve_weights(months: int = 12) -> list[float]:
    raw = [0.04, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.11, 0.10, 0.07, 0.05]
    if months != 12:
        step = 1.0 / months
        raw = [step] * months
    total = sum(raw)
    return [w / total for w in raw[:months]]


def _build_skurve_cumulative(gesamtbudget: float, months: int = 12) -> list[int]:
    weights = _skurve_weights(months)
    gb = round(gesamtbudget)
    cumul = 0.0
    skurve: list[int] = []
    for i, w in enumerate(weights):
        if i == len(weights) - 1:
            skurve.append(gb)
        else:
            cumul += gb * w
            skurve.append(round(cumul))
    return skurve


def build_budget_skeleton(
    psp_content: str,
    *,
    project_title: str = "",
    project_type: str = "other",
    budget_ceiling_chf: float | None = None,
) -> BudgetSkeleton:
    work_packages = parse_psp_work_packages(psp_content)
    if not work_packages:
        raise ValueError(
            "Im Projektstrukturplan (PSP) wurden keine Arbeitspakete erkannt. "
            "Bitte zuerst Schritt 3 (PSP) mit PT-Angaben erstellen."
        )

    rates = rates_for_project_type(project_type)
    role_pt: dict[str, int] = {}
    for wp in work_packages:
        pt = parse_pt_effort(wp.effort_pt)
        if pt <= 0:
            continue
        role = (wp.responsible or "Sonstige").strip()
        role_pt[role] = role_pt.get(role, 0) + pt

    if not role_pt:
        raise ValueError("PSP enthält keine PT-Angaben — Budgetplan benötigt Aufwandsspalte.")

    role_lines: list[RoleBudgetLine] = []
    for role, pt in sorted(role_pt.items(), key=lambda x: -x[1]):
        key = role_rate_key(role)
        rate = rates.get(key, rates["default"])
        role_lines.append(RoleBudgetLine(role=role, pt=pt, rate_chf=rate))

    total_pt = sum(r.pt for r in role_lines)
    personal_chf = round(sum(r.total_chf for r in role_lines), 2)
    sachkosten = _default_sachkosten(project_type, personal_chf)
    sachkosten_chf = round(sum(x[2] for x in sachkosten), 2)
    base = personal_chf + sachkosten_chf
    reserve_pct = rates.get("reserve_pct", 0.12)
    reserve_chf = round(base * reserve_pct, 2)
    gesamtbudget = round(base + reserve_chf, 2)

    phases = group_by_phase(work_packages)
    phase_costs: list[tuple[str, float]] = []
    for phase in phases:
        phase_pt = sum(parse_pt_effort(wp.effort_pt) for wp in phase.work_packages)
        if phase_pt <= 0 or total_pt <= 0:
            continue
        share = phase_pt / total_pt
        phase_costs.append((phase.name, round(personal_chf * share, 2)))

    return BudgetSkeleton(
        project_title=project_title.strip() or "Projekt",
        project_type=project_type,
        role_lines=role_lines,
        sachkosten=sachkosten,
        phase_costs=phase_costs,
        total_pt=total_pt,
        personal_chf=personal_chf,
        sachkosten_chf=sachkosten_chf,
        reserve_chf=reserve_chf,
        gesamtbudget=gesamtbudget,
        skurve=_build_skurve_cumulative(gesamtbudget),
        budget_ceiling_chf=budget_ceiling_chf,
    )


def render_budgetplan_markdown(skeleton: BudgetSkeleton) -> str:
    gb = skeleton.gesamtbudget
    base = skeleton.personal_chf + skeleton.sachkosten_chf
    reserve_pct = int(round(skeleton.reserve_chf / max(base, 1) * 100))
    title = skeleton.project_title

    lines: list[str] = [
        f'## Budgetplan für das Projekt "{title}"',
        "",
        "> Berechnung: **deterministisch aus PSP (Schritt 3)** — PT × CHF-Sätze nach Projekttyp "
        f"`{skeleton.project_type}`. Gesamt-PT: **{skeleton.total_pt}**.",
        "",
    ]
    if skeleton.budget_ceiling_chf:
        lines.append(
            f"> Budgetdeckel (Budgetbasis): **{_format_chf(skeleton.budget_ceiling_chf)} CHF** — "
            f"geschätzt **{_format_chf(gb)} CHF**."
        )
        lines.append("")

    lines.extend(
        [
            "### 1. Aufwandsbasis (aus PSP)",
            "",
            "| Rolle | PT | Quelle |",
            "|-------|-----|--------|",
        ]
    )
    for rl in skeleton.role_lines:
        lines.append(f"| {rl.role} | {_format_qty(rl.pt)} | PSP Schritt 3 |")
    lines.append(f"| **Gesamt** | **{_format_qty(skeleton.total_pt)}** | |")
    lines.extend(
        [
            "",
            "### 2. Kostenarten",
            "",
            "| Kostenart | Beschreibung | Menge | Einheit | CHF/Einheit | Gesamt CHF |",
            "|-----------|--------------|-------|---------|-------------|------------|",
            "| **Personalkosten** | | | | | |",
        ]
    )
    for rl in skeleton.role_lines:
        lines.append(
            f"| {rl.role} | aus PSP | {_format_qty(rl.pt)} | PT | {_format_qty(rl.rate_chf)} | "
            f"{_format_chf(rl.total_chf)} |"
        )
    if skeleton.sachkosten:
        lines.append("| **Sachkosten** | | | | | |")
        for name, desc, amount in skeleton.sachkosten:
            lines.append(
                f"| {name} | {desc} | 1 | Pauschale | {_format_chf(amount)} | {_format_chf(amount)} |"
            )
    lines.append(
        f"| **Reserve ({reserve_pct}%)** | Risikoreserve | | | | {_format_chf(skeleton.reserve_chf)} |"
    )
    lines.append(f"| **Gesamtbudget** | | | | | **{_format_chf(gb)}** |")
    lines.extend(
        [
            "",
            "### 3. Kosten pro Projektphase",
            "",
            "| Projektphase | Kosten CHF |",
            "|--------------|------------|",
        ]
    )
    for phase_name, cost in skeleton.phase_costs:
        lines.append(f"| {phase_name} | {_format_chf(cost)} |")
    lines.append(f"| **Total Personal** | **{_format_chf(skeleton.personal_chf)}** |")
    lines.extend(
        [
            "",
            "### 4. S-Kurve (kumuliert, 12 Monate)",
            "",
            "| Monat | Kumuliert CHF |",
            "|-------|---------------|",
        ]
    )
    for idx, cumul in enumerate(skeleton.skurve, start=1):
        lines.append(f"| Monat {idx} | {_format_chf(cumul)} |")
    lines.extend(
        [
            "",
            "### 5. Gesamtbudget",
            "",
            f"**Gesamtbudget: {_format_chf(gb)} CHF**",
            "",
        ]
    )
    return "\n".join(lines)


def build_budgetplan_from_psp(
    psp_content: str,
    *,
    project_title: str = "",
    project_type: str = "other",
    budget_ceiling_chf: float | None = None,
) -> str:
    skeleton = build_budget_skeleton(
        psp_content,
        project_title=project_title,
        project_type=project_type,
        budget_ceiling_chf=budget_ceiling_chf,
    )
    return render_budgetplan_markdown(skeleton)
