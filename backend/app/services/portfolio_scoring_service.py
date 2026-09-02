"""Portfolio-Scoring (SI, FE, WSJF, Tier) — Logik aus pm-suite, neu gebaut."""

from __future__ import annotations

from typing import Any

from app.core.crypto.portfolio_fields import portfolio_name, read_financial, write_financial
from app.models import PortfolioProject

REFERENCE_DURATION_MONTHS = 6.0


class PortfolioScoringService:
    @staticmethod
    def derive_roi_pct(npv: int, cost_total: int) -> int:
        if cost_total <= 0:
            return 0
        return round((npv / cost_total) * 100)

    @classmethod
    def sync_derived_financial_metrics(cls, project: PortfolioProject) -> None:
        fin = read_financial(project)
        roi = cls.derive_roi_pct(fin["financial_npv"], fin["cost_total"])
        write_financial(
            project,
            financial_npv=fin["financial_npv"],
            financial_roi_pct=roi,
            payback_months=fin["payback_months"],
            cost_total=fin["cost_total"],
        )

    @staticmethod
    def effective_job_size(project: PortfolioProject) -> float:
        job_size = max(project.job_size or 1, 1)
        duration = project.duration_months or 0
        if duration > 0:
            return max(job_size * (duration / REFERENCE_DURATION_MONTHS), 1.0)
        return float(job_size)

    @staticmethod
    def calculate_strategic_importance(project: PortfolioProject) -> float:
        base = (
            0.6 * (project.strategic_alignment_score or 0)
            + 0.2 * (project.nonfinancial_benefit_score or 0)
            + 0.2 * (project.customer_impact_score or 0)
        )
        compliance_bonus = {
            "Mandatory": 1.5,
            "High": 1.0,
            "Medium": 0.5,
            "Low": 0.2,
            "None": 0.0,
        }.get(project.compliance_criticality or "", 0.0)
        score = ((base + compliance_bonus) / 6.5) * 100
        return min(100.0, max(0.0, score))

    @staticmethod
    def calculate_feasibility_index(project: PortfolioProject) -> float:
        feasibility = project.feasibility_score or 0
        complexity = project.complexity_score or 0
        resource_penalty = min(project.resource_demand_fte or 0, 10)
        raw = (feasibility + (5 - complexity) + (10 - resource_penalty)) / 3
        return min(100.0, max(0.0, (raw / 5) * 100))

    @classmethod
    def calculate_value_score(cls, project: PortfolioProject) -> float:
        fin = read_financial(project)
        roi = cls.derive_roi_pct(fin["financial_npv"], fin["cost_total"])
        npv = fin["financial_npv"]
        payback = fin["payback_months"] or 36
        cost = fin["cost_total"] or 1
        roi_component = min(roi / 5, 40)
        npv_normalized = min((npv / cost) * 20, 40) if cost > 0 else 0
        payback_normalized = max(40 - (payback * 40 / 36), 0)
        score = (roi_component + npv_normalized + payback_normalized) / 3
        return min(100.0, max(0.0, score))

    @classmethod
    def calculate_wsjf(cls, project: PortfolioProject) -> float:
        value = (project.customer_impact_score or 0) + (project.nonfinancial_benefit_score or 0)
        job_size = cls.effective_job_size(project)
        wsjf = (
            (value + (project.time_criticality or 0) + (project.risk_reduction_opportunity or 0))
            / job_size
        )
        return round(wsjf, 2)

    @staticmethod
    def calculate_composite_score(project: PortfolioProject) -> float:
        si = project.strategic_importance or 0
        fe = project.feasibility_index or 0
        vs = project.value_score or 0
        complexity_penalty = ((5 - (project.complexity_score or 0)) / 5) * 100
        score = 0.35 * si + 0.30 * fe + 0.25 * vs + 0.10 * complexity_penalty
        return min(100.0, max(0.0, score))

    @staticmethod
    def assign_tier(strategic_importance: float, feasibility_index: float) -> str:
        if strategic_importance >= 70 and feasibility_index >= 60:
            return "A"
        if strategic_importance < 50 or feasibility_index < 40:
            return "C"
        return "B"

    @staticmethod
    def assign_matrix_quadrant(strategic_importance: float, feasibility_index: float) -> str:
        high_si = strategic_importance >= 50
        high_fe = feasibility_index >= 50
        if high_si and high_fe:
            return "quick_wins"
        if high_si and not high_fe:
            return "strategic_longterm"
        if not high_si and high_fe:
            return "quick_easy"
        return "low_priority"

    @classmethod
    def calculate_all_scores(cls, project: PortfolioProject) -> PortfolioProject:
        cls.sync_derived_financial_metrics(project)
        project.strategic_importance = cls.calculate_strategic_importance(project)
        project.feasibility_index = cls.calculate_feasibility_index(project)
        project.value_score = cls.calculate_value_score(project)
        project.wsjf = cls.calculate_wsjf(project)
        project.composite_score = cls.calculate_composite_score(project)
        project.tier = cls.assign_tier(project.strategic_importance, project.feasibility_index)
        project.matrix_quadrant = cls.assign_matrix_quadrant(
            project.strategic_importance,
            project.feasibility_index,
        )
        return project

    @classmethod
    def get_matrix_data(cls, projects: list[PortfolioProject]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for project in projects:
            if project.strategic_importance is None or project.feasibility_index is None:
                cls.calculate_all_scores(project)
            tier = cls.assign_tier(
                project.strategic_importance or 0,
                project.feasibility_index or 0,
            )
            project.tier = tier
            project.matrix_quadrant = cls.assign_matrix_quadrant(
                project.strategic_importance or 0,
                project.feasibility_index or 0,
            )
            size_npv = max(read_financial(project)["financial_npv"], 0)
            fin = read_financial(project)
            result.append(
                {
                    "id": str(project.id),
                    "display_number": project.display_number,
                    "project_key": project.project.key if project.project else None,
                    "name": portfolio_name(project),
                    "x": project.feasibility_index,
                    "y": project.strategic_importance,
                    "size_npv": size_npv,
                    "tier": tier,
                    "matrix_quadrant": project.matrix_quadrant,
                    "category": project.category,
                    "wsjf": project.wsjf,
                    "composite_score": project.composite_score,
                    "cost_total": fin["cost_total"],
                }
            )
        return result

    @classmethod
    def get_wsjf_ranking(cls, projects: list[PortfolioProject]) -> list[dict[str, Any]]:
        for project in projects:
            if project.wsjf is None:
                cls.calculate_all_scores(project)
        sorted_projects = sorted(
            projects,
            key=lambda p: (
                -(p.wsjf or 0),
                -(p.strategic_importance or 0),
                read_financial(p)["cost_total"],
                str(p.id),
            ),
        )
        ranking: list[dict[str, Any]] = []
        for rank, project in enumerate(sorted_projects, start=1):
            fin = read_financial(project)
            ranking.append(
                {
                    "rank": rank,
                    "id": str(project.id),
                    "name": portfolio_name(project),
                    "project_key": project.project.key if project.project else None,
                    "wsjf": project.wsjf,
                    "tier": project.tier,
                    "category": project.category,
                    "strategic_importance": project.strategic_importance,
                    "cost_total": fin["cost_total"],
                }
            )
        return ranking
