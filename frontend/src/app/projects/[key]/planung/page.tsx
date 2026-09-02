"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Loader2,
  Pencil,
  Save,
  Sparkles,
  Table,
  X,
} from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PlanningDocumentPanel } from "@/components/planning/PlanningDocumentPanel";
import { PlanningStepNav } from "@/components/planning/PlanningStepNav";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  confirmBudgetBasis,
  fetchPlanning,
  fetchProjectByKey,
  fetchPspAnalysis,
  generatePlanningArtifact,
  generateJiraCsvFromPsp,
  generateProjectIdea,
  savePlanningArtifact,
  saveProjectIdea,
  setPlanningArtifactStatus,
  updateBudgetBasis,
  updateProject,
  type PlanningState,
  type Project,
  type PspAnalysis,
} from "@/lib/api";
import {
  PLANNING_FLOW_STEPS,
  PLANNING_IDEA,
  type PlanningStepKey,
} from "@/lib/planning-steps";
import { WIZARD_PROJECT_TYPE_LABELS, type WizardProjectType } from "@/lib/project-types";

export default function PlanningPage() {
  const params = useParams();
  const projectKey = params.key as string;

  const [project, setProject] = useState<Project | null>(null);
  const [planning, setPlanning] = useState<PlanningState | null>(null);
  const [activeStep, setActiveStep] = useState<PlanningStepKey>(PLANNING_IDEA.key);
  const [draftContent, setDraftContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [pspAnalysis, setPspAnalysis] = useState<PspAnalysis | null>(null);
  const [budgetCeiling, setBudgetCeiling] = useState("");
  const [budgetNotes, setBudgetNotes] = useState("");
  const [budgetLoading, setBudgetLoading] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [nameSaving, setNameSaving] = useState(false);
  const [contentMode, setContentMode] = useState<"read" | "edit">("read");
  const [showPreview, setShowPreview] = useState(false);

  const load = useCallback(async () => {
    if (!projectKey) return;
    setLoading(true);
    setError(null);
    try {
      const [p, s] = await Promise.all([
        fetchProjectByKey(projectKey),
        fetchPlanning(projectKey),
      ]);
      setProject(p);
      setPlanning(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }, [projectKey]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (activeStep !== "psp" || !planning) {
      setPspAnalysis(null);
      return;
    }
    const ceiling = planning.budget_basis?.budget_ceiling_chf;
    if (ceiling != null) setBudgetCeiling(String(ceiling));
    setBudgetLoading(true);
    fetchPspAnalysis(projectKey)
      .then(setPspAnalysis)
      .catch((err) => setError(err instanceof Error ? err.message : "PSP-Auswertung fehlgeschlagen"))
      .finally(() => setBudgetLoading(false));
  }, [activeStep, planning, projectKey]);

  const activeMeta = useMemo(
    () => PLANNING_FLOW_STEPS.find((s) => s.key === activeStep) ?? PLANNING_FLOW_STEPS[0],
    [activeStep]
  );

  useEffect(() => {
    if (!planning) return;
    if (activeStep === PLANNING_IDEA.key) {
      setDraftContent(planning.project_idea);
      return;
    }
    const artifact = planning.artifacts.find((a) => a.slug === activeStep);
    setDraftContent(artifact?.content ?? "");
  }, [activeStep, planning]);

  useEffect(() => {
    setContentMode("read");
    setShowPreview(false);
  }, [activeStep]);

  function stepFilled(key: PlanningStepKey): boolean {
    if (!planning) return false;
    if (key === PLANNING_IDEA.key) return planning.completion.has_project_idea;
    return planning.artifacts.find((a) => a.slug === key)?.has_content ?? false;
  }

  function stepStatus(key: PlanningStepKey): string {
    if (key === PLANNING_IDEA.key) {
      return planning?.completion.has_project_idea ? "draft" : "pending";
    }
    return planning?.artifacts.find((a) => a.slug === key)?.status ?? "pending";
  }

  async function onSave() {
    if (!planning) return;
    setSaving(true);
    setError(null);
    try {
      if (activeStep === PLANNING_IDEA.key) {
        const updated = await saveProjectIdea(projectKey, draftContent, planning.revision);
        setPlanning(updated);
      } else {
        const artifact = planning.artifacts.find((a) => a.slug === activeStep);
        const updated = await savePlanningArtifact(
          projectKey,
          activeStep,
          draftContent,
          artifact?.version ?? 0
        );
        setPlanning(updated);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function onGenerate() {
    if (!planning) return;
    setGenerating(true);
    setError(null);
    try {
      let updated: PlanningState;
      if (activeStep === PLANNING_IDEA.key) {
        updated = await generateProjectIdea(
          projectKey,
          planning.revision,
          draftContent.trim() || undefined
        );
      } else {
        updated = await generatePlanningArtifact(
          projectKey,
          activeStep,
          planning.revision
        );
      }
      setPlanning(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "KI-Generierung fehlgeschlagen");
    } finally {
      setGenerating(false);
    }
  }

  async function onStatusChange(status: "pending" | "draft" | "approved") {
    if (!planning || activeStep === PLANNING_IDEA.key) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await setPlanningArtifactStatus(projectKey, activeStep, status);
      setPlanning(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status konnte nicht gesetzt werden");
    } finally {
      setSaving(false);
    }
  }

  const canGenerateKi =
    activeStep === PLANNING_IDEA.key ||
    ["zielplanung", "projektbeschrieb", "psp"].includes(activeStep);

  const canGenerateFromPsp = activeStep === "jira_csv";

  async function onGenerateFromPsp() {
    if (!planning) return;
    setGenerating(true);
    setError(null);
    try {
      const updated = await generateJiraCsvFromPsp(projectKey, planning.revision);
      setPlanning(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Jira-CSV-Generierung fehlgeschlagen");
    } finally {
      setGenerating(false);
    }
  }

  async function onSaveBudgetBasis() {
    if (!planning) return;
    setBudgetLoading(true);
    setError(null);
    try {
      const ceiling = budgetCeiling.trim() ? parseFloat(budgetCeiling) : null;
      const result = await updateBudgetBasis(projectKey, {
        budget_ceiling_chf: ceiling,
        notes: budgetNotes,
        expected_revision: planning.revision,
      });
      setPlanning(result.planning);
      setPspAnalysis(result.analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Budgetbasis konnte nicht gespeichert werden");
    } finally {
      setBudgetLoading(false);
    }
  }

  async function onConfirmBudgetBasis() {
    if (!planning) return;
    setBudgetLoading(true);
    setError(null);
    try {
      const updated = await confirmBudgetBasis(projectKey, planning.revision);
      setPlanning(updated);
      const analysis = await fetchPspAnalysis(projectKey);
      setPspAnalysis(analysis);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Budgetbasis konnte nicht bestätigt werden");
    } finally {
      setBudgetLoading(false);
    }
  }

  function startNameEdit() {
    if (!project) return;
    setNameDraft(project.name);
    setEditingName(true);
  }

  function cancelNameEdit() {
    setEditingName(false);
    setNameDraft("");
  }

  async function saveNameEdit() {
    if (!project) return;
    const trimmed = nameDraft.trim();
    if (!trimmed) {
      setError("Projektname darf nicht leer sein.");
      return;
    }
    if (trimmed === project.name) {
      cancelNameEdit();
      return;
    }
    setNameSaving(true);
    setError(null);
    try {
      const updated = await updateProject(project.id, {
        name: trimmed,
        version: project.version,
      });
      setProject(updated);
      cancelNameEdit();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Name konnte nicht gespeichert werden");
    } finally {
      setNameSaving(false);
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <PageContainer>
          <p className="text-center text-muted-foreground py-16">Planung wird geladen…</p>
        </PageContainer>
      </AppLayout>
    );
  }

  if (error && !planning) {
    return (
      <AppLayout>
        <PageContainer width="narrow">
          <p className="text-destructive mb-4">{error}</p>
          <Button variant="outline" asChild>
            <Link href="/projects">Zurück zu Projekten</Link>
          </Button>
        </PageContainer>
      </AppLayout>
    );
  }

  const typeLabel =
    project?.project_type &&
    project.project_type in WIZARD_PROJECT_TYPE_LABELS
      ? WIZARD_PROJECT_TYPE_LABELS[project.project_type as WizardProjectType]
      : project?.project_type;

  return (
    <AppLayout>
      <PageContainer width="wide">
        <div className="mb-6">
          <Link
            href="/projects"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Projekte
          </Link>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-mono text-muted-foreground mb-1">{projectKey}</p>
              {editingName ? (
                <div className="flex flex-wrap items-center gap-2 max-w-xl">
                  <Input
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    className="font-display text-lg font-semibold h-10"
                    maxLength={256}
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") void saveNameEdit();
                      if (e.key === "Escape") cancelNameEdit();
                    }}
                  />
                  <Button
                    type="button"
                    size="sm"
                    onClick={() => void saveNameEdit()}
                    disabled={nameSaving}
                  >
                    {nameSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    Speichern
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={cancelNameEdit}
                    disabled={nameSaving}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h1 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight">
                    {project?.name ?? "Planung"}
                  </h1>
                  {project && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground"
                      onClick={startNameEdit}
                      title="Projektname bearbeiten"
                    >
                      <Pencil className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              )}
              {typeLabel && (
                <p className="text-sm text-muted-foreground mt-1">{typeLabel}</p>
              )}
            </div>
            {planning && (
              <div className="rounded-xl border border-border/70 bg-card/80 px-4 py-2 text-sm">
                <span className="text-muted-foreground">Fortschritt: </span>
                <span className="font-medium">
                  {planning.completion.filled_count}/{planning.completion.total_count}
                </span>
              </div>
            )}
          </div>
        </div>

        {error && <InlineAlert className="mb-4">{error}</InlineAlert>}

        <div className="grid lg:grid-cols-[280px_1fr] gap-6">
          <PlanningStepNav
            activeStep={activeStep}
            onSelect={setActiveStep}
            stepFilled={stepFilled}
            stepStatus={stepStatus}
          />

          <div className="space-y-4">
            <PlanningDocumentPanel
              title={`${activeMeta.displayNumber}. ${activeMeta.label}`}
              description={activeMeta.description}
              status={activeStep === PLANNING_IDEA.key ? undefined : stepStatus(activeStep)}
              content={
                activeStep === PLANNING_IDEA.key
                  ? planning?.project_idea ?? ""
                  : planning?.artifacts.find((a) => a.slug === activeStep)?.content ?? ""
              }
              draftContent={draftContent}
              onDraftChange={setDraftContent}
              contentMode={contentMode}
              onContentModeChange={setContentMode}
              showPreview={showPreview}
              onShowPreviewChange={setShowPreview}
              placeholder={
                activeStep === PLANNING_IDEA.key
                  ? "Beschreibe die Projektidee…"
                  : "Markdown-Inhalt…"
              }
            >
              {activeStep === "psp" && (
                <div className="mb-6 rounded-xl border border-border/70 bg-muted/20 p-4 space-y-4">
                  <h3 className="font-display text-base font-semibold">Budgetauswertung (Phase 5)</h3>
                  {budgetLoading && !pspAnalysis ? (
                    <p className="text-sm text-muted-foreground">Auswertung läuft…</p>
                  ) : pspAnalysis ? (
                    <>
                      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                        <div>
                          <p className="text-muted-foreground">Arbeitspakete</p>
                          <p className="font-medium">{pspAnalysis.work_package_count}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Personentage</p>
                          <p className="font-medium">{pspAnalysis.total_pt} PT</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Geschätzt gesamt</p>
                          <p className="font-medium">
                            CHF {pspAnalysis.estimated_total_chf.toLocaleString("de-CH")}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Status</p>
                          <p className="font-medium">{pspAnalysis.status}</p>
                        </div>
                      </div>
                      {pspAnalysis.fits_ceiling === false && (
                        <InlineAlert variant="info">
                          Budgetdeckel überschritten um CHF{" "}
                          {pspAnalysis.deviation_chf?.toLocaleString("de-CH")} (
                          {pspAnalysis.deviation_pct}%)
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
                            onChange={(e) => setBudgetCeiling(e.target.value)}
                            placeholder="z. B. 120000"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="budgetNotes">Notizen</Label>
                          <Input
                            id="budgetNotes"
                            value={budgetNotes}
                            onChange={(e) => setBudgetNotes(e.target.value)}
                            placeholder="Optional"
                          />
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={budgetLoading}
                          onClick={onSaveBudgetBasis}
                        >
                          Budgetbasis speichern
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          disabled={budgetLoading}
                          onClick={onConfirmBudgetBasis}
                        >
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
              )}
            </PlanningDocumentPanel>

            <div className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-4 flex flex-wrap items-center gap-2">
              <Button type="button" onClick={onSave} disabled={saving}>
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Speichern
              </Button>
              {canGenerateFromPsp && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onGenerateFromPsp}
                  disabled={generating || saving}
                >
                  {generating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Table className="w-4 h-4" />
                  )}
                  Aus PSP generieren
                </Button>
              )}
              {canGenerateKi && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={onGenerate}
                  disabled={generating || saving}
                >
                  {generating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4" />
                  )}
                  Mit KI generieren
                </Button>
              )}
              {activeStep !== PLANNING_IDEA.key && (
                <>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={saving}
                    onClick={() => onStatusChange("draft")}
                  >
                    Als Entwurf
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={saving}
                    onClick={() => onStatusChange("approved")}
                  >
                    Freigeben
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
