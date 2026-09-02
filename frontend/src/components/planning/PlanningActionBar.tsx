"use client";

import { FileDown, Loader2, Save, Sparkles, Table } from "lucide-react";
import { Button } from "@/components/ui/button";
import { planningArtifactExportDocxUrl } from "@/lib/api";
import { PLANNING_IDEA, type PlanningStepKey } from "@/lib/planning-steps";
import { canGenerateFromPsp, canGenerateKi } from "@/lib/planning-capabilities";

export function PlanningActionBar({
  projectKey,
  activeStep,
  saving,
  generating,
  hasContent,
  onSave,
  onGenerateKi,
  onGenerateFromPsp,
  onSetDraft,
  onSetApproved,
}: {
  projectKey: string;
  activeStep: PlanningStepKey;
  saving: boolean;
  generating: boolean;
  hasContent: boolean;
  onSave: () => void;
  onGenerateKi: () => void;
  onGenerateFromPsp: () => void;
  onSetDraft: () => void;
  onSetApproved: () => void;
}) {
  const canExportStep = activeStep !== PLANNING_IDEA.key && hasContent;

  return (
    <div className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-4 flex flex-wrap items-center gap-2">
      <Button type="button" onClick={onSave} disabled={saving}>
        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Speichern
      </Button>
      {canGenerateFromPsp(activeStep) && (
        <Button
          type="button"
          variant="secondary"
          onClick={onGenerateFromPsp}
          disabled={generating || saving}
        >
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Table className="w-4 h-4" />}
          Aus PSP generieren
        </Button>
      )}
      {canGenerateKi(activeStep) && (
        <Button
          type="button"
          variant="secondary"
          onClick={onGenerateKi}
          disabled={generating || saving}
        >
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Mit KI generieren
        </Button>
      )}
      {canExportStep && (
        <Button
          type="button"
          variant="outline"
          onClick={() =>
            window.open(planningArtifactExportDocxUrl(projectKey, activeStep), "_blank")
          }
        >
          <FileDown className="w-4 h-4" />
          Word (.docx)
        </Button>
      )}
      {activeStep !== PLANNING_IDEA.key && (
        <>
          <Button type="button" variant="outline" size="sm" disabled={saving} onClick={onSetDraft}>
            Als Entwurf
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={saving} onClick={onSetApproved}>
            Freigeben
          </Button>
        </>
      )}
    </div>
  );
}
