"use client";

import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { PspAnalysis } from "@/lib/api";

export function PspBudgetPanel({
  analysis,
  loading,
  budgetCeiling,
  budgetNotes,
  onBudgetCeilingChange,
  onBudgetNotesChange,
  onSave,
  onConfirm,
}: {
  analysis: PspAnalysis | null;
  loading: boolean;
  budgetCeiling: string;
  budgetNotes: string;
  onBudgetCeilingChange: (value: string) => void;
  onBudgetNotesChange: (value: string) => void;
  onSave: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="mb-6 rounded-xl border border-border/70 bg-muted/20 p-4 space-y-4">
      <h3 className="font-display text-base font-semibold">Budgetauswertung (Phase 5)</h3>
      {loading && !analysis ? (
        <p className="text-sm text-muted-foreground">Auswertung läuft…</p>
      ) : analysis ? (
        <>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-muted-foreground">Arbeitspakete</p>
              <p className="font-medium">{analysis.work_package_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Personentage</p>
              <p className="font-medium">{analysis.total_pt} PT</p>
            </div>
            <div>
              <p className="text-muted-foreground">Geschätzt gesamt</p>
              <p className="font-medium">CHF {analysis.estimated_total_chf.toLocaleString("de-CH")}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Status</p>
              <p className="font-medium">{analysis.status}</p>
            </div>
          </div>
          {analysis.fits_ceiling === false && (
            <InlineAlert variant="info">
              Budgetdeckel überschritten um CHF {analysis.deviation_chf?.toLocaleString("de-CH")} (
              {analysis.deviation_pct}%)
            </InlineAlert>
          )}
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="budgetCeiling">Budgetdeckel (CHF)</Label>
              <Input
                id="budgetCeiling"
                type="number"
                min={0}
                value={budgetCeiling}
                onChange={(e) => onBudgetCeilingChange(e.target.value)}
                placeholder="z. B. 120000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="budgetNotes">Notizen</Label>
              <Input
                id="budgetNotes"
                value={budgetNotes}
                onChange={(e) => onBudgetNotesChange(e.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" size="sm" disabled={loading} onClick={onSave}>
              Budgetbasis speichern
            </Button>
            <Button type="button" variant="outline" size="sm" disabled={loading} onClick={onConfirm}>
              Budgetbasis bestätigen
            </Button>
          </div>
        </>
      ) : (
        <p className="text-sm text-muted-foreground">
          PSP-Tabelle mit AP-IDs und PT ausfüllen, dann erscheint die Auswertung.
        </p>
      )}
    </div>
  );
}
