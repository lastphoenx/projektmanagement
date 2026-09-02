import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function WizardStepIndicator({
  steps,
  currentStep,
}: {
  steps: readonly string[];
  currentStep: number;
}) {
  return (
    <div className="flex gap-2 mb-8">
      {steps.map((label, index) => (
        <div
          key={label}
          className={cn(
            "flex-1 rounded-xl border px-3 py-2.5 text-center text-xs font-medium transition-colors",
            index === currentStep
              ? "border-primary bg-primary/10 text-primary"
              : index < currentStep
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-border/70 bg-card/50 text-muted-foreground"
          )}
        >
          {index < currentStep ? <Check className="w-3 h-3 inline mr-1" /> : null}
          {index + 1}. {label}
        </div>
      ))}
    </div>
  );
}
