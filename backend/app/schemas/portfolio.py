"""Pydantic-Schemas für Portfolio."""

from pydantic import BaseModel, Field


class PortfolioProjectBase(BaseModel):
    name: str = Field(..., max_length=200)
    sponsor: str | None = Field(None, max_length=100)
    business_unit: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=50)
    objective_1: str | None = Field(None, max_length=200)
    objective_2: str | None = Field(None, max_length=200)
    objective_3: str | None = Field(None, max_length=200)
    strategic_alignment_score: int = Field(default=0, ge=0, le=5)
    nonfinancial_benefit_score: int = Field(default=0, ge=0, le=5)
    customer_impact_score: int = Field(default=0, ge=0, le=5)
    feasibility_score: int = Field(default=0, ge=0, le=5)
    complexity_score: int = Field(default=0, ge=0, le=5)
    risk_score: int = Field(default=0, ge=0, le=5)
    cybersecurity_risk_score: int = Field(default=0, ge=0, le=5)
    compliance_criticality: str | None = Field(None, max_length=50)
    data_privacy_level: str | None = Field(None, max_length=50)
    financial_npv: int = Field(default=0)
    financial_roi_pct: int = Field(default=0)
    payback_months: int = Field(default=0, ge=0)
    cost_total: int = Field(default=0, ge=0)
    time_criticality: int = Field(default=0, ge=0, le=5)
    risk_reduction_opportunity: int = Field(default=0, ge=0, le=5)
    job_size: int = Field(default=1, ge=1)
    dependencies_count: int = Field(default=0, ge=0)
    duration_months: int = Field(default=0, ge=0)
    resource_demand_fte: int = Field(default=0, ge=0)


class PortfolioProjectCreateRequest(PortfolioProjectBase):
    project_key: str = Field(..., min_length=2, max_length=8)


class PortfolioProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=200)
    sponsor: str | None = Field(None, max_length=100)
    business_unit: str | None = Field(None, max_length=100)
    category: str | None = Field(None, max_length=50)
    objective_1: str | None = Field(None, max_length=200)
    objective_2: str | None = Field(None, max_length=200)
    objective_3: str | None = Field(None, max_length=200)
    strategic_alignment_score: int | None = Field(None, ge=0, le=5)
    nonfinancial_benefit_score: int | None = Field(None, ge=0, le=5)
    customer_impact_score: int | None = Field(None, ge=0, le=5)
    feasibility_score: int | None = Field(None, ge=0, le=5)
    complexity_score: int | None = Field(None, ge=0, le=5)
    risk_score: int | None = Field(None, ge=0, le=5)
    cybersecurity_risk_score: int | None = Field(None, ge=0, le=5)
    compliance_criticality: str | None = Field(None, max_length=50)
    data_privacy_level: str | None = Field(None, max_length=50)
    financial_npv: int | None = None
    payback_months: int | None = Field(None, ge=0)
    cost_total: int | None = Field(None, ge=0)
    time_criticality: int | None = Field(None, ge=0, le=5)
    risk_reduction_opportunity: int | None = Field(None, ge=0, le=5)
    job_size: int | None = Field(None, ge=1)
    dependencies_count: int | None = Field(None, ge=0)
    duration_months: int | None = Field(None, ge=0)
    resource_demand_fte: int | None = Field(None, ge=0)


class PortfolioProjectResponse(PortfolioProjectBase):
    id: str
    project_id: str
    project_key: str | None
    display_number: int
    strategic_importance: float | None
    feasibility_index: float | None
    value_score: float | None
    wsjf: float | None
    composite_score: float | None
    tier: str | None
    matrix_quadrant: str | None
    created_at: str
    updated_at: str


class PortfolioEligibleProjectResponse(BaseModel):
    project_id: str
    project_key: str
    name: str
    is_complete: bool
    filled_count: int
    total_count: int
    missing_labels: list[str]
    can_manage: bool
