"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  Loader2,
  Save,
  Sparkles,
} from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import {
  fetchPlanning,
  fetchProjectByKey,
  generatePlanningArtifact,
  generateProjectIdea,
  savePlanningArtifact,
  saveProjectIdea,
  setPlanningArtifactStatus,
  type PlanningState,
  type Project,
} from "@/lib/api";
import {
  PLANNING_FLOW_STEPS,
  PLANNING_IDEA,
  STATUS_LABELS,
  type PlanningStepKey,
} from "@/lib/planning-steps";
import { WIZARD_PROJECT_TYPE_LABELS, type WizardProjectType } from "@/lib/project-types";
import { cn } from "@/lib/utils";

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

  const canGenerateKi =
    activeStep === PLANNING_IDEA.key ||
    ["zielplanung", "projektbeschrieb", "psp"].includes(activeStep);

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
              <h1 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight">
                {project?.name ?? "Planung"}
              </h1>
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

        {error && (
          <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2 mb-4">
            {error}
          </p>
        )}

        <div className="grid lg:grid-cols-[280px_1fr] gap-6">
          <aside className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-3 h-fit lg:sticky lg:top-20">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground px-2 py-2">
              Planungsschritte
            </p>
            <nav className="space-y-1">
              {PLANNING_FLOW_STEPS.map((step) => {
                const filled = stepFilled(step.key);
                const status = stepStatus(step.key);
                const Icon = step.icon;
                return (
                  <button
                    key={step.key}
                    type="button"
                    onClick={() => setActiveStep(step.key)}
                    className={cn(
                      "w-full flex items-start gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                      activeStep === step.key
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-muted/60"
                    )}
                  >
                    <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {step.displayNumber}. {step.shortLabel}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {STATUS_LABELS[status] ?? status}
                      </p>
                    </div>
                    {filled ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    ) : (
                      <Circle className="w-4 h-4 text-muted-foreground/40 shrink-0" />
                    )}
                  </button>
                );
              })}
            </nav>
          </aside>

          <section className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-5 sm:p-6">
            <div className="mb-4">
              <h2 className="font-display text-xl font-semibold">
                {activeMeta.displayNumber}. {activeMeta.label}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">{activeMeta.description}</p>
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Bearbeiten
                </label>
                <textarea
                  value={draftContent}
                  onChange={(e) => setDraftContent(e.target.value)}
                  rows={18}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm font-mono leading-relaxed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder={
                    activeStep === PLANNING_IDEA.key
                      ? "Beschreibe die Projektidee…"
                      : "Markdown-Inhalt…"
                  }
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Vorschau
                </label>
                <div className="rounded-lg border border-border/70 bg-muted/30 px-3 py-2 text-sm min-h-[22.5rem] max-h-[22.5rem] overflow-auto whitespace-pre-wrap">
                  {draftContent.trim() ? draftContent : (
                    <span className="text-muted-foreground">Noch kein Inhalt.</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button type="button" onClick={onSave} disabled={saving}>
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Speichern
              </Button>
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
          </section>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
