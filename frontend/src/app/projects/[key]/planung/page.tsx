"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PlanningActionBar } from "@/components/planning/PlanningActionBar";
import { PlanningCompletionBanner } from "@/components/planning/PlanningCompletionBanner";
import { PlanningDocumentPanel } from "@/components/planning/PlanningDocumentPanel";
import { PlanningPageHeader } from "@/components/planning/PlanningPageHeader";
import { PlanningStepNav } from "@/components/planning/PlanningStepNav";
import { PspBudgetPanel } from "@/components/planning/PspBudgetPanel";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { usePlanningPage } from "@/hooks/usePlanningPage";
import { PLANNING_IDEA } from "@/lib/planning-steps";
import { WIZARD_PROJECT_TYPE_LABELS, type WizardProjectType } from "@/lib/project-types";

export default function PlanningPage() {
  const params = useParams();
  const projectKey = params.key as string;
  const vm = usePlanningPage(projectKey);

  const typeLabel =
    vm.project?.project_type && vm.project.project_type in WIZARD_PROJECT_TYPE_LABELS
      ? WIZARD_PROJECT_TYPE_LABELS[vm.project.project_type as WizardProjectType]
      : vm.project?.project_type;

  if (vm.loading) {
    return (
      <AppLayout>
        <PageContainer>
          <p className="text-center text-muted-foreground py-16">Planung wird geladen…</p>
        </PageContainer>
      </AppLayout>
    );
  }

  if (vm.error && !vm.planning) {
    return (
      <AppLayout>
        <PageContainer width="narrow">
          <p className="text-destructive mb-4">{vm.error}</p>
          <Button variant="outline" asChild>
            <Link href="/projects">Zurück zu Projekten</Link>
          </Button>
        </PageContainer>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageContainer width="wide">
        <PlanningPageHeader
          projectKey={projectKey}
          project={vm.project}
          typeLabel={typeLabel}
          editingName={vm.editingName}
          nameDraft={vm.nameDraft}
          nameSaving={vm.nameSaving}
          onNameDraftChange={vm.setNameDraft}
          onStartNameEdit={vm.startNameEdit}
          onCancelNameEdit={vm.cancelNameEdit}
          onSaveNameEdit={() => void vm.saveNameEdit()}
        />

        {vm.planning && (
          <PlanningCompletionBanner completion={vm.planning.completion} className="mb-4" />
        )}

        {vm.error && <InlineAlert className="mb-4">{vm.error}</InlineAlert>}

        <div className="grid lg:grid-cols-[280px_1fr] gap-6">
          <PlanningStepNav
            activeStep={vm.activeStep}
            onSelect={vm.setActiveStep}
            stepFilled={vm.stepFilled}
            stepStatus={vm.stepStatus}
            filledCount={vm.planning?.completion.filled_count}
            totalCount={vm.planning?.completion.total_count}
          />

          <div className="space-y-4">
            <PlanningDocumentPanel
              title={`${vm.activeMeta.displayNumber}. ${vm.activeMeta.label}`}
              description={vm.activeMeta.description}
              status={vm.activeStep === PLANNING_IDEA.key ? undefined : vm.stepStatus(vm.activeStep)}
              content={vm.savedContent}
              draftContent={vm.draftContent}
              onDraftChange={vm.setDraftContent}
              contentMode={vm.contentMode}
              onContentModeChange={vm.setContentMode}
              showPreview={vm.showPreview}
              onShowPreviewChange={vm.setShowPreview}
              placeholder={
                vm.activeStep === PLANNING_IDEA.key
                  ? "Beschreibe die Projektidee…"
                  : "Markdown-Inhalt…"
              }
            >
              {vm.activeStep === "psp" && (
                <PspBudgetPanel
                  analysis={vm.pspAnalysis}
                  loading={vm.budgetLoading}
                  budgetCeiling={vm.budgetCeiling}
                  budgetNotes={vm.budgetNotes}
                  onBudgetCeilingChange={vm.setBudgetCeiling}
                  onBudgetNotesChange={vm.setBudgetNotes}
                  onSave={() => void vm.saveBudgetBasis()}
                  onConfirm={() => void vm.confirmBudget()}
                />
              )}
            </PlanningDocumentPanel>

            <PlanningActionBar
              activeStep={vm.activeStep}
              saving={vm.saving}
              generating={vm.generating}
              onSave={() => void vm.persistContent()}
              onGenerateKi={() => void vm.generateKi()}
              onGenerateFromPsp={() => void vm.generateFromPsp()}
              onSetDraft={() => void vm.setArtifactStatus("draft")}
              onSetApproved={() => void vm.setArtifactStatus("approved")}
            />
          </div>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
