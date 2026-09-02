"use client";

import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { PlanningCompletion } from "@/lib/api";
import { cn } from "@/lib/utils";

export function PlanningCompletionBanner({
  completion,
  className,
}: {
  completion: PlanningCompletion;
  className?: string;
}) {
  const pct = Math.round((completion.filled_count / completion.total_count) * 100);

  if (completion.is_complete) {
    return (
      <div
        className={cn(
          "rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-950",
          className
        )}
      >
        <p className="font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          Planung vollständig ({completion.filled_count}/{completion.total_count})
        </p>
        <div className="mt-2 h-1.5 rounded-full bg-emerald-200 overflow-hidden">
          <div className="h-full bg-emerald-600 rounded-full" style={{ width: "100%" }} />
        </div>
        {completion.is_fully_approved ? (
          <p className="text-xs text-emerald-800 mt-2">
            Alle Dokumente freigegeben — bereit für Portfolio und erweiterte KI-Schritte.
          </p>
        ) : (
          <p className="text-xs text-emerald-800 mt-2">
            Inhalt vollständig; {completion.approved_count}/{completion.total_count} freigegeben.
          </p>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950",
        className
      )}
    >
      <p className="font-medium flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
        Planung unvollständig ({completion.filled_count}/{completion.total_count})
      </p>
      <div className="mt-2 h-1.5 rounded-full bg-amber-200 overflow-hidden">
        <div
          className="h-full bg-amber-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      {completion.missing_labels.length > 0 && (
        <>
          <p className="text-xs mt-2 mb-1 text-amber-900">Es fehlen noch:</p>
          <ul className="text-xs list-disc list-inside space-y-0.5 ml-1 text-amber-900">
            {completion.missing_labels.map((label) => (
              <li key={label}>{label}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
