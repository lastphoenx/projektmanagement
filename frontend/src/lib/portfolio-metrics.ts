/** Abgeleitete Portfolio-Kennzahlen (Spiegel der Backend-Logik für UI-Vorschau). */

const REFERENCE_DURATION_MONTHS = 6;

const COMPLIANCE_BONUS: Record<string, number> = {
  Mandatory: 1.5,
  High: 1.0,
  Medium: 0.5,
  Low: 0.2,
  None: 0.0,
};

export function deriveRoiPct(npv: number, costTotal: number): number {
  if (costTotal <= 0) return 0;
  return Math.round((npv / costTotal) * 100);
}

export function linkFinancialFields(
  prev: { financial_npv: number; cost_total: number },
  field: "financial_npv" | "cost_total",
  rawValue: number
): { financial_npv: number; cost_total: number } {
  const value = Math.max(0, rawValue);

  if (field === "financial_npv") {
    return { financial_npv: value, cost_total: prev.cost_total };
  }

  if (value <= 0) {
    return { financial_npv: prev.financial_npv, cost_total: value };
  }

  if (prev.cost_total <= 0) {
    return { financial_npv: prev.financial_npv, cost_total: value };
  }

  const roi = deriveRoiPct(prev.financial_npv, prev.cost_total);
  const financial_npv = roi > 0 ? Math.round((value * roi) / 100) : prev.financial_npv;
  return { financial_npv, cost_total: value };
}

export function effectiveJobSize(jobSize: number, durationMonths: number): number {
  const size = Math.max(jobSize || 1, 1);
  if (durationMonths > 0) {
    return Math.max(size * (durationMonths / REFERENCE_DURATION_MONTHS), 1);
  }
  return size;
}

export function previewStrategicImportance(params: {
  strategicAlignment: number;
  nonfinancialBenefit: number;
  customerImpact: number;
  complianceCriticality: string;
}): number {
  const base =
    0.6 * params.strategicAlignment +
    0.2 * params.nonfinancialBenefit +
    0.2 * params.customerImpact;
  const bonus = COMPLIANCE_BONUS[params.complianceCriticality] ?? 0;
  const score = ((base + bonus) / 6.5) * 100;
  return Math.min(100, Math.max(0, score));
}

export function previewFeasibilityIndex(params: {
  feasibility: number;
  complexity: number;
  resourceDemandFte: number;
}): number {
  const resourcePenalty = Math.min(params.resourceDemandFte, 10);
  const raw =
    (params.feasibility + (5 - params.complexity) + (10 - resourcePenalty)) / 3;
  return Math.min(100, Math.max(0, (raw / 5) * 100));
}

export function previewWsjf(params: {
  nonfinancialBenefit: number;
  customerImpact: number;
  timeCriticality: number;
  riskReduction: number;
  jobSize: number;
  durationMonths: number;
}): number {
  const cod =
    params.nonfinancialBenefit +
    params.customerImpact +
    params.timeCriticality +
    params.riskReduction;
  const size = effectiveJobSize(params.jobSize, params.durationMonths);
  return Math.round((cod / size) * 100) / 100;
}

export function assignPortfolioTier(
  strategicImportance: number,
  feasibilityIndex: number
): "A" | "B" | "C" {
  if (strategicImportance >= 70 && feasibilityIndex >= 60) return "A";
  if (strategicImportance < 50 || feasibilityIndex < 40) return "C";
  return "B";
}

export function tierLabel(tier: string): string {
  switch (tier) {
    case "A":
      return "Quick Wins";
    case "B":
      return "Moderate Priority";
    case "C":
      return "Backlog";
    default:
      return tier;
  }
}

export function tierColorClass(tier: string): string {
  switch (tier) {
    case "A":
      return "bg-green-100 text-green-800 border-green-300";
    case "B":
      return "bg-yellow-100 text-yellow-800 border-yellow-300";
    case "C":
      return "bg-red-100 text-red-800 border-red-300";
    default:
      return "bg-gray-100 text-gray-800 border-gray-300";
  }
}

export function categoryIcon(category: string | null | undefined): string {
  switch (category) {
    case "Transform":
      return "🚀";
    case "Grow":
      return "📈";
    case "Run":
      return "⚙️";
    default:
      return "📁";
  }
}

export function formatChf(value: number): string {
  if (value >= 1_000_000) return `CHF ${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `CHF ${(value / 1_000).toFixed(0)}k`;
  return `CHF ${value.toFixed(0)}`;
}
