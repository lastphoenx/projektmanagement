"use client";

import { CheckCircle2, Circle } from "lucide-react";
import {
  PLANNING_FLOW_STEPS,
  STATUS_LABELS,
  type PlanningStepKey,
} from "@/lib/planning-steps";
import { cn } from "@/lib/utils";

export function PlanningStepNav({
  activeStep,
  onSelect,
  stepFilled,
  stepStatus,
}: {
  activeStep: PlanningStepKey;
  onSelect: (key: PlanningStepKey) => void;
  stepFilled: (key: PlanningStepKey) => boolean;
  stepStatus: (key: PlanningStepKey) => string;
}) {
  return (
    <aside className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-3 h-fit lg:sticky lg:top-20">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground px-2 py-2">
        Planungsschritte
      </p>
      <nav className="space-y-1">
        {PLANNING_FLOW_STEPS.map((step) => {
          const filled = stepFilled(step.key);
          const status = stepStatus(step.key);
          const Icon = step.icon;
          const isActive = activeStep === step.key;
          return (
            <button
              key={step.key}
              type="button"
              onClick={() => onSelect(step.key)}
              className={cn(
                "w-full flex items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                isActive ? "bg-primary/10 text-primary" : "hover:bg-muted/60"
              )}
            >
              <span
                className={cn(
                  "planning-step-icon flex h-8 w-8 items-center justify-center rounded-lg shrink-0 mt-0.5",
                  filled ? "planning-step-icon-done" : "planning-step-icon-pending"
                )}
              >
                <Icon className="w-4 h-4" />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">
                  {step.displayNumber}. {step.shortLabel}
                </p>
                <p className={cn("text-xs", isActive ? "text-primary/80" : "text-muted-foreground")}>
                  {STATUS_LABELS[status] ?? status}
                </p>
              </div>
              {filled ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-1" />
              ) : (
                <Circle className="w-4 h-4 text-muted-foreground/40 shrink-0 mt-1" />
              )}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
