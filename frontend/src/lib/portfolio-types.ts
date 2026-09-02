export type PortfolioProject = {
  id: string;
  project_id: string;
  project_key: string | null;
  display_number: number;
  name: string;
  sponsor: string | null;
  business_unit: string | null;
  category: string | null;
  objective_1: string | null;
  objective_2: string | null;
  objective_3: string | null;
  strategic_alignment_score: number;
  nonfinancial_benefit_score: number;
  customer_impact_score: number;
  feasibility_score: number;
  complexity_score: number;
  risk_score: number;
  cybersecurity_risk_score: number;
  compliance_criticality: string | null;
  data_privacy_level: string | null;
  financial_npv: number;
  financial_roi_pct: number;
  payback_months: number;
  cost_total: number;
  time_criticality: number;
  risk_reduction_opportunity: number;
  job_size: number;
  dependencies_count: number;
  duration_months: number;
  resource_demand_fte: number;
  strategic_importance: number | null;
  feasibility_index: number | null;
  value_score: number | null;
  wsjf: number | null;
  composite_score: number | null;
  tier: string | null;
  matrix_quadrant: string | null;
  created_at: string;
  updated_at: string;
};

export type PortfolioMatrixPoint = {
  id: string;
  display_number: number;
  project_key: string | null;
  name: string;
  x: number;
  y: number;
  size_npv: number;
  tier: string;
  matrix_quadrant: string | null;
  category: string | null;
  wsjf: number | null;
  composite_score: number | null;
  cost_total: number | null;
};

export type PortfolioWsjfItem = {
  rank: number;
  id: string;
  name: string;
  project_key: string | null;
  wsjf: number | null;
  tier: string | null;
  category: string | null;
  strategic_importance: number | null;
  cost_total: number | null;
};

export type PortfolioEligibleProject = {
  project_id: string;
  project_key: string;
  name: string;
  is_complete: boolean;
  filled_count: number;
  total_count: number;
  missing_labels: string[];
  can_manage: boolean;
};

export type PortfolioFormData = {
  name: string;
  sponsor: string;
  business_unit: string;
  category: string;
  objective_1: string;
  objective_2: string;
  objective_3: string;
  strategic_alignment_score: number;
  nonfinancial_benefit_score: number;
  customer_impact_score: number;
  feasibility_score: number;
  complexity_score: number;
  risk_score: number;
  cybersecurity_risk_score: number;
  compliance_criticality: string;
  data_privacy_level: string;
  financial_npv: number;
  payback_months: number;
  cost_total: number;
  time_criticality: number;
  risk_reduction_opportunity: number;
  job_size: number;
  dependencies_count: number;
  duration_months: number;
  resource_demand_fte: number;
};

export const INITIAL_PORTFOLIO_FORM: PortfolioFormData = {
  name: "",
  sponsor: "",
  business_unit: "",
  category: "Transform",
  objective_1: "",
  objective_2: "",
  objective_3: "",
  strategic_alignment_score: 0,
  nonfinancial_benefit_score: 0,
  customer_impact_score: 0,
  feasibility_score: 0,
  complexity_score: 0,
  risk_score: 0,
  cybersecurity_risk_score: 0,
  compliance_criticality: "Medium",
  data_privacy_level: "Internal",
  financial_npv: 0,
  payback_months: 0,
  cost_total: 0,
  time_criticality: 0,
  risk_reduction_opportunity: 0,
  job_size: 1,
  dependencies_count: 0,
  duration_months: 0,
  resource_demand_fte: 0,
};

export function portfolioToFormData(entry: PortfolioProject): PortfolioFormData {
  return {
    name: entry.name,
    sponsor: entry.sponsor ?? "",
    business_unit: entry.business_unit ?? "",
    category: entry.category ?? "Transform",
    objective_1: entry.objective_1 ?? "",
    objective_2: entry.objective_2 ?? "",
    objective_3: entry.objective_3 ?? "",
    strategic_alignment_score: entry.strategic_alignment_score,
    nonfinancial_benefit_score: entry.nonfinancial_benefit_score,
    customer_impact_score: entry.customer_impact_score,
    feasibility_score: entry.feasibility_score,
    complexity_score: entry.complexity_score,
    risk_score: entry.risk_score,
    cybersecurity_risk_score: entry.cybersecurity_risk_score,
    compliance_criticality: entry.compliance_criticality ?? "Medium",
    data_privacy_level: entry.data_privacy_level ?? "Internal",
    financial_npv: entry.financial_npv,
    payback_months: entry.payback_months,
    cost_total: entry.cost_total,
    time_criticality: entry.time_criticality,
    risk_reduction_opportunity: entry.risk_reduction_opportunity,
    job_size: entry.job_size,
    dependencies_count: entry.dependencies_count,
    duration_months: entry.duration_months,
    resource_demand_fte: entry.resource_demand_fte,
  };
}
