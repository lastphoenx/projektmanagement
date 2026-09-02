"""Portfolio-CRUD mit Completion-Gate und RBAC."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.core.auth.rbac import ProjectRole, get_user_project_role, require_role
from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.core.crypto.portfolio_fields import (
    apply_sensitive_fields,
    read_financial,
    sensitive_fields_to_dict,
)
from app.models import PortfolioProject, Project, User
from app.services.audit import log_event
from app.services.planning_completion_service import assess_planning_completion
from app.services.planning_service import ensure_planning_framework, get_planning_state
from app.services.portfolio_scoring_service import PortfolioScoringService
from app.services.project_service import (
    _accessible_projects_query,
    get_project_entity_by_key,
)


class PortfolioError(Exception):
    def __init__(self, message: str, code: str = "portfolio_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def _portfolio_query(db: Session, user: User):
    q = (
        db.query(PortfolioProject)
        .join(Project, PortfolioProject.project_id == Project.id)
        .filter(PortfolioProject.tenant_id == user.tenant_id)
        .options(joinedload(PortfolioProject.project))
    )
    if user.is_admin:
        return q
    accessible = _accessible_projects_query(db, user).with_entities(Project.id).subquery()
    return q.filter(PortfolioProject.project_id.in_(accessible))


def _next_display_number(db: Session, tenant_id: uuid.UUID) -> int:
    current = (
        db.query(PortfolioProject.display_number)
        .filter(PortfolioProject.tenant_id == tenant_id)
        .order_by(PortfolioProject.display_number.desc())
        .first()
    )
    return (current[0] if current else 0) + 1


def _to_dict(entry: PortfolioProject) -> dict[str, Any]:
    project_key = entry.project.key if entry.project else None
    sensitive = sensitive_fields_to_dict(entry)
    return {
        "id": str(entry.id),
        "project_id": str(entry.project_id),
        "project_key": project_key,
        "display_number": entry.display_number,
        **sensitive,
        "strategic_alignment_score": entry.strategic_alignment_score,
        "nonfinancial_benefit_score": entry.nonfinancial_benefit_score,
        "customer_impact_score": entry.customer_impact_score,
        "feasibility_score": entry.feasibility_score,
        "complexity_score": entry.complexity_score,
        "risk_score": entry.risk_score,
        "cybersecurity_risk_score": entry.cybersecurity_risk_score,
        "compliance_criticality": entry.compliance_criticality,
        "data_privacy_level": entry.data_privacy_level,
        "time_criticality": entry.time_criticality,
        "risk_reduction_opportunity": entry.risk_reduction_opportunity,
        "job_size": entry.job_size,
        "dependencies_count": entry.dependencies_count,
        "duration_months": entry.duration_months,
        "resource_demand_fte": entry.resource_demand_fte,
        "strategic_importance": entry.strategic_importance,
        "feasibility_index": entry.feasibility_index,
        "value_score": entry.value_score,
        "wsjf": entry.wsjf,
        "composite_score": entry.composite_score,
        "tier": entry.tier,
        "matrix_quadrant": entry.matrix_quadrant,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
    }


def _require_entry(db: Session, user: User, entry_id: uuid.UUID) -> PortfolioProject:
    entry = (
        _portfolio_query(db, user)
        .filter(PortfolioProject.id == entry_id)
        .first()
    )
    if not entry:
        raise PortfolioError("Portfolio-Eintrag nicht gefunden", "not_found")
    return entry


def _assert_planning_complete(db: Session, user: User, project: Project) -> None:
    ensure_planning_framework(db, project)
    state = get_planning_state(db, user, project)
    completion = assess_planning_completion(state["project_idea"], state["artifacts"])
    if not completion["is_complete"]:
        raise PortfolioError(
            "Portfolio-Aufnahme erst möglich, wenn alle Planungsschritte ausgefüllt sind",
            "planning_incomplete",
        )


def list_portfolio_entries(db: Session, user: User) -> list[dict[str, Any]]:
    entries = _portfolio_query(db, user).order_by(PortfolioProject.display_number).all()
    return [_to_dict(e) for e in entries]


def get_portfolio_entry(db: Session, user: User, entry_id: uuid.UUID) -> dict[str, Any]:
    return _to_dict(_require_entry(db, user, entry_id))


def get_portfolio_by_project_key(db: Session, user: User, project_key: str) -> dict[str, Any] | None:
    project = get_project_entity_by_key(db, user, project_key)
    entry = (
        _portfolio_query(db, user)
        .filter(PortfolioProject.project_id == project.id)
        .first()
    )
    return _to_dict(entry) if entry else None


def create_portfolio_entry(
    db: Session,
    user: User,
    *,
    project_key: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    project = get_project_entity_by_key(db, user, project_key)
    require_role(db, user, project, ProjectRole.MANAGER)

    existing = db.query(PortfolioProject).filter(PortfolioProject.project_id == project.id).first()
    if existing:
        raise PortfolioError("Projekt ist bereits im Portfolio", "already_exists")

    _assert_planning_complete(db, user, project)

    default_name = decrypt_text_master(project.name_encrypted)
    entry = PortfolioProject(
        tenant_id=user.tenant_id,
        project_id=project.id,
        display_number=_next_display_number(db, user.tenant_id),
        name_encrypted=encrypt_text_master(data.get("name") or default_name),
        business_unit=data.get("business_unit"),
        category=data.get("category"),
        strategic_alignment_score=data.get("strategic_alignment_score", 0),
        nonfinancial_benefit_score=data.get("nonfinancial_benefit_score", 0),
        customer_impact_score=data.get("customer_impact_score", 0),
        feasibility_score=data.get("feasibility_score", 0),
        complexity_score=data.get("complexity_score", 0),
        risk_score=data.get("risk_score", 0),
        cybersecurity_risk_score=data.get("cybersecurity_risk_score", 0),
        compliance_criticality=data.get("compliance_criticality"),
        data_privacy_level=data.get("data_privacy_level"),
        time_criticality=data.get("time_criticality", 0),
        risk_reduction_opportunity=data.get("risk_reduction_opportunity", 0),
        job_size=max(data.get("job_size", 1), 1),
        dependencies_count=data.get("dependencies_count", 0),
        duration_months=data.get("duration_months", 0),
        resource_demand_fte=data.get("resource_demand_fte", 0),
    )
    apply_sensitive_fields(
        entry,
        {
            "sponsor": data.get("sponsor"),
            "objective_1": data.get("objective_1"),
            "objective_2": data.get("objective_2"),
            "objective_3": data.get("objective_3"),
            "financial_npv": data.get("financial_npv", 0),
            "payback_months": data.get("payback_months", 0),
            "cost_total": data.get("cost_total", 0),
        },
    )
    PortfolioScoringService.calculate_all_scores(entry)
    db.add(entry)
    db.flush()
    db.refresh(entry)
    entry.project = project
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="portfolio.create",
        resource_type="portfolio_project",
        resource_id=entry.id,
        detail=f"project_key={project.key}",
    )
    return _to_dict(entry)


def update_portfolio_entry(
    db: Session,
    user: User,
    entry_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    entry = _require_entry(db, user, entry_id)
    require_role(db, user, entry.project, ProjectRole.MANAGER)

    for field in (
        "business_unit",
        "category",
        "strategic_alignment_score",
        "nonfinancial_benefit_score",
        "customer_impact_score",
        "feasibility_score",
        "complexity_score",
        "risk_score",
        "cybersecurity_risk_score",
        "compliance_criticality",
        "data_privacy_level",
        "time_criticality",
        "risk_reduction_opportunity",
        "job_size",
        "dependencies_count",
        "duration_months",
        "resource_demand_fte",
    ):
        if field in data and data[field] is not None:
            setattr(entry, field, data[field])
    apply_sensitive_fields(entry, data)
    if "job_size" in data and data["job_size"] is not None:
        entry.job_size = max(data["job_size"], 1)

    PortfolioScoringService.calculate_all_scores(entry)
    db.flush()
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="portfolio.update",
        resource_type="portfolio_project",
        resource_id=entry.id,
    )
    return _to_dict(entry)


def delete_portfolio_entry(db: Session, user: User, entry_id: uuid.UUID) -> None:
    entry = _require_entry(db, user, entry_id)
    require_role(db, user, entry.project, ProjectRole.MANAGER)
    db.delete(entry)
    log_event(
        db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="portfolio.delete",
        resource_type="portfolio_project",
        resource_id=entry_id,
    )


def get_matrix_data(db: Session, user: User) -> list[dict[str, Any]]:
    entries = _portfolio_query(db, user).all()
    return PortfolioScoringService.get_matrix_data(entries)


def get_wsjf_ranking(db: Session, user: User) -> list[dict[str, Any]]:
    entries = _portfolio_query(db, user).all()
    return PortfolioScoringService.get_wsjf_ranking(entries)


def list_eligible_projects(db: Session, user: User) -> list[dict[str, Any]]:
    """Projekte ohne Portfolio-Eintrag, mit Completion-Status."""
    projects = _accessible_projects_query(db, user).order_by(Project.key).all()
    portfolio_project_ids = {
        row[0]
        for row in db.query(PortfolioProject.project_id)
        .filter(PortfolioProject.tenant_id == user.tenant_id)
        .all()
    }
    result: list[dict[str, Any]] = []
    for project in projects:
        if project.id in portfolio_project_ids:
            continue
        if get_user_project_role(db, user, project) is None:
            continue
        role = get_user_project_role(db, user, project)
        can_manage = user.is_admin or role in (ProjectRole.MANAGER, ProjectRole.OWNER)
        try:
            state = get_planning_state(db, user, project)
            completion = assess_planning_completion(state["project_idea"], state["artifacts"])
        except Exception:
            completion = {"is_complete": False, "filled_count": 0, "total_count": 11, "missing_labels": []}
        result.append(
            {
                "project_id": str(project.id),
                "project_key": project.key,
                "name": decrypt_text_master(project.name_encrypted),
                "is_complete": completion["is_complete"],
                "filled_count": completion["filled_count"],
                "total_count": completion["total_count"],
                "missing_labels": completion.get("missing_labels", []),
                "can_manage": can_manage,
            }
        )
    return result
