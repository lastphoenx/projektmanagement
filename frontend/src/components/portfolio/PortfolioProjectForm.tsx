"use client";

import { ChangeEvent } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  assignPortfolioTier,
  deriveRoiPct,
  linkFinancialFields,
  previewFeasibilityIndex,
  previewStrategicImportance,
  previewWsjf,
} from "@/lib/portfolio-metrics";
import type { PortfolioFormData } from "@/lib/portfolio-types";

const SCORE_FIELDS = new Set([
  "strategic_alignment_score",
  "nonfinancial_benefit_score",
  "customer_impact_score",
  "feasibility_score",
  "complexity_score",
  "risk_score",
  "cybersecurity_risk_score",
  "time_criticality",
  "risk_reduction_opportunity",
]);

const NUMERIC_FIELDS = new Set([
  "financial_npv",
  "payback_months",
  "cost_total",
  "job_size",
  "dependencies_count",
  "duration_months",
  "resource_demand_fte",
]);

function clampScore(value: string): number {
  const n = Number(value);
  if (Number.isNaN(n)) return 0;
  return Math.min(5, Math.max(0, Math.round(n)));
}

interface PortfolioProjectFormProps {
  formData: PortfolioFormData;
  onChange: (data: PortfolioFormData) => void;
}

export function PortfolioProjectForm({ formData, onChange }: PortfolioProjectFormProps) {
  function handleChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) {
    const { name, value } = event.target;

    if (name === "financial_npv" || name === "cost_total") {
      const num = Math.max(0, Number(value) || 0);
      onChange({
        ...formData,
        ...linkFinancialFields(
          { financial_npv: formData.financial_npv, cost_total: formData.cost_total },
          name,
          num
        ),
      });
      return;
    }

    onChange({
      ...formData,
      [name]: SCORE_FIELDS.has(name)
        ? clampScore(value)
        : NUMERIC_FIELDS.has(name)
          ? Math.max(0, Number(value) || 0)
          : value,
    });
  }

  const derivedRoi = deriveRoiPct(formData.financial_npv, formData.cost_total);
  const si = previewStrategicImportance({
    strategicAlignment: formData.strategic_alignment_score,
    nonfinancialBenefit: formData.nonfinancial_benefit_score,
    customerImpact: formData.customer_impact_score,
    complianceCriticality: formData.compliance_criticality,
  });
  const fe = previewFeasibilityIndex({
    feasibility: formData.feasibility_score,
    complexity: formData.complexity_score,
    resourceDemandFte: formData.resource_demand_fte,
  });
  const liveWsjf = previewWsjf({
    nonfinancialBenefit: formData.nonfinancial_benefit_score,
    customerImpact: formData.customer_impact_score,
    timeCriticality: formData.time_criticality,
    riskReduction: formData.risk_reduction_opportunity,
    jobSize: formData.job_size,
    durationMonths: formData.duration_months,
  });
  const liveTier = assignPortfolioTier(si, fe);

  return (
    <div className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Stammdaten</CardTitle>
            <CardDescription>Grundlegende Projektdaten und Einordnung</CardDescription>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <Field label="Projektname *" name="name" value={formData.name} onChange={handleChange} />
            <Field label="Sponsor" name="sponsor" value={formData.sponsor} onChange={handleChange} />
            <Field label="Business Unit" name="business_unit" value={formData.business_unit} onChange={handleChange} />
            <SelectField label="Kategorie" name="category" value={formData.category} onChange={handleChange}>
              <option value="Run">Run</option>
              <option value="Grow">Grow</option>
              <option value="Transform">Transform</option>
            </SelectField>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ziele</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <TextareaField label="Ziel 1" name="objective_1" value={formData.objective_1} onChange={handleChange} />
            <TextareaField label="Ziel 2" name="objective_2" value={formData.objective_2} onChange={handleChange} />
            <TextareaField label="Ziel 3" name="objective_3" value={formData.objective_3} onChange={handleChange} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bewertungsparameter</CardTitle>
            <CardDescription>Scores von 0 bis 5</CardDescription>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <NumberField label="Strategische Ausrichtung" name="strategic_alignment_score" value={formData.strategic_alignment_score} onChange={handleChange} />
            <NumberField label="Non-Financial Benefit" name="nonfinancial_benefit_score" value={formData.nonfinancial_benefit_score} onChange={handleChange} />
            <NumberField label="Kunden-Impact" name="customer_impact_score" value={formData.customer_impact_score} onChange={handleChange} />
            <NumberField label="Machbarkeit" name="feasibility_score" value={formData.feasibility_score} onChange={handleChange} />
            <NumberField label="Komplexität" name="complexity_score" value={formData.complexity_score} onChange={handleChange} />
            <NumberField label="Risiko" name="risk_score" value={formData.risk_score} onChange={handleChange} />
            <NumberField label="Cybersecurity-Risiko" name="cybersecurity_risk_score" value={formData.cybersecurity_risk_score} onChange={handleChange} />
            <NumberField label="Zeitkritikalität" name="time_criticality" value={formData.time_criticality} onChange={handleChange} />
            <NumberField label="Risk Reduction Opportunity" name="risk_reduction_opportunity" value={formData.risk_reduction_opportunity} onChange={handleChange} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Finanzen und Aufwand</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <NumberField label="NPV (CHF)" name="financial_npv" value={formData.financial_npv} onChange={handleChange} step={1000} />
            <ReadOnly label="ROI (abgeleitet)" value={`${derivedRoi}%`} />
            <NumberField label="Payback (Monate)" name="payback_months" value={formData.payback_months} onChange={handleChange} />
            <NumberField label="Gesamtkosten (CHF)" name="cost_total" value={formData.cost_total} onChange={handleChange} step={1000} />
            <NumberField label="Job Size" name="job_size" value={formData.job_size} onChange={handleChange} min={1} />
            <NumberField label="Abhängigkeiten" name="dependencies_count" value={formData.dependencies_count} onChange={handleChange} />
            <NumberField label="Dauer (Monate)" name="duration_months" value={formData.duration_months} onChange={handleChange} />
            <NumberField label="Ressourcenbedarf (FTE)" name="resource_demand_fte" value={formData.resource_demand_fte} onChange={handleChange} />
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <SelectField label="Compliance-Kritikalität" name="compliance_criticality" value={formData.compliance_criticality} onChange={handleChange}>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Mandatory">Mandatory</option>
            </SelectField>
            <SelectField label="Datenschutz-Level" name="data_privacy_level" value={formData.data_privacy_level} onChange={handleChange}>
              <option value="Public">Public</option>
              <option value="Internal">Internal</option>
              <option value="Confidential">Confidential</option>
            </SelectField>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live-Vorschau</CardTitle>
            <CardDescription>Aus aktuellen Formularwerten</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <ReadOnly label="Strategic Importance" value={`${si.toFixed(1)}%`} />
            <ReadOnly label="Feasibility Index" value={`${fe.toFixed(1)}%`} />
            <ReadOnly label="WSJF" value={liveWsjf.toFixed(2)} />
            <ReadOnly label="Tier (Vorschau)" value={liveTier} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({
  label,
  name,
  value,
  onChange,
}: {
  label: string;
  name: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} name={name} value={value} onChange={onChange} />
    </div>
  );
}

function TextareaField({
  label,
  name,
  value,
  onChange,
}: {
  label: string;
  name: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <textarea
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        rows={2}
        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
    </div>
  );
}

function SelectField({
  label,
  name,
  value,
  onChange,
  children,
}: {
  label: string;
  name: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLSelectElement>) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <select
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {children}
      </select>
    </div>
  );
}

function NumberField({
  label,
  name,
  value,
  onChange,
  min = 0,
  max,
  step = 1,
}: {
  label: string;
  name: string;
  value: number;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <Input
        id={name}
        name={name}
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={onChange}
      />
    </div>
  );
}

function ReadOnly({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-border/50 pb-2 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
