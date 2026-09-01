"""PSP-Auswertung und Budgetbasis (Phase 5)."""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.auth.rbac import ProjectRole, require_role
from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.models import PlanningFramework, Project, User
from app.services.planning_service import PlanningError, ensure_planning_framework, get_planning_state
from app.services.project_type_service import rates_for_project_type, role_rate_key
from app.services.psp_parse_service import parse_psp_work_packages, parse_pt_effort


def _load_budget_basis(framework: PlanningFramework) -> dict:
    raw = decrypt_text_master(framework.budget_basis_encrypted) if framework.budget_basis_encrypted else ""
    if not raw:
        return {"status": "draft"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"status": "draft"}


def _save_budget_basis(framework: PlanningFramework, data: dict) -> None:
    framework.budget_basis_encrypted = encrypt_text_master(json.dumps(data, ensure_ascii=False))


def analyze_psp_budget(db: Session, user: User, project: Project) -> dict:
    require_role(db, user, project, ProjectRole.VIEWER)
    state = get_planning_state(db, user, project)
    psp = next((a for a in state["artifacts"] if a["slug"] == "psp"), None)
    if not psp or not psp["content"].strip():
        raise PlanningError("PSP (Schritt 3) benötigt Inhalt für die Auswertung", "missing_psp")

    packages = parse_psp_work_packages(psp["content"])
    if not packages:
        raise PlanningError("Keine Arbeitspakete im PSP erkannt — Tabelle mit AP-ID und PT prüfen", "parse_failed")

    rates = rates_for_project_type(project.project_type)
    role_lines: dict[str, int] = {}
    total_pt = 0
    for wp in packages:
        pt = parse_pt_effort(wp.effort_pt)
        total_pt += pt
        role = role_rate_key(wp.responsible)
        role_lines[role] = role_lines.get(role, 0) + pt

    personal_chf = 0.0
    role_detail = []
    for role, pt in role_lines.items():
        rate = rates.get(role, rates["default"])
        line_total = pt * rate
        personal_chf += line_total
        role_detail.append({"role": role, "pt": pt, "rate_chf": rate, "total_chf": round(line_total, 2)})

    sachkosten_chf = round(personal_chf * 0.08, 2)
    subtotal = personal_chf + sachkosten_chf
    reserve_chf = round(subtotal * rates["reserve_pct"], 2)
    estimated_total = round(subtotal + reserve_chf, 2)

    framework = ensure_planning_framework(db, project)
    basis = _load_budget_basis(framework)
    ceiling = basis.get("budget_ceiling_chf")

    analysis = {
        "total_pt": total_pt,
        "personal_chf": round(personal_chf, 2),
        "sachkosten_chf": sachkosten_chf,
        "reserve_chf": reserve_chf,
        "estimated_total_chf": estimated_total,
        "role_lines": role_detail,
        "work_package_count": len(packages),
        "status": basis.get("status", "draft"),
        "budget_ceiling_chf": ceiling,
    }
    if ceiling and ceiling > 0:
        deviation = estimated_total - ceiling
        analysis["deviation_chf"] = round(deviation, 2)
        analysis["deviation_pct"] = round((deviation / ceiling) * 100, 1)
        analysis["fits_ceiling"] = estimated_total <= ceiling

    return analysis


def update_budget_basis(
    db: Session,
    user: User,
    project: Project,
    *,
    budget_ceiling_chf: float | None,
    notes: str,
    expected_revision: int,
) -> dict:
    require_role(db, user, project, ProjectRole.MEMBER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    basis = _load_budget_basis(framework)
    analysis = analyze_psp_budget(db, user, project)
    basis.update(
        {
            "status": basis.get("status", "draft"),
            "estimated_total_chf": analysis["estimated_total_chf"],
            "personal_chf": analysis["personal_chf"],
            "sachkosten_chf": analysis["sachkosten_chf"],
            "reserve_chf": analysis["reserve_chf"],
            "total_pt": analysis["total_pt"],
            "budget_ceiling_chf": budget_ceiling_chf,
            "notes": notes,
        }
    )
    _save_budget_basis(framework, basis)
    framework.revision += 1
    db.flush()
    state = get_planning_state(db, user, project)
    return {"analysis": analysis, "planning": state}


def confirm_budget_basis(
    db: Session,
    user: User,
    project: Project,
    *,
    expected_revision: int,
) -> dict:
    require_role(db, user, project, ProjectRole.MANAGER)
    framework = ensure_planning_framework(db, project)
    if framework.revision != expected_revision:
        raise PlanningError("Konflikt – Planung wurde zwischenzeitlich geändert", "version_conflict")

    basis = _load_budget_basis(framework)
    analysis = analyze_psp_budget(db, user, project)
    basis.update(
        {
            "status": "confirmed",
            "estimated_total_chf": analysis["estimated_total_chf"],
            "personal_chf": analysis["personal_chf"],
            "sachkosten_chf": analysis["sachkosten_chf"],
            "reserve_chf": analysis["reserve_chf"],
            "total_pt": analysis["total_pt"],
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_budget_basis(framework, basis)
    framework.revision += 1
    db.flush()
    return get_planning_state(db, user, project)
