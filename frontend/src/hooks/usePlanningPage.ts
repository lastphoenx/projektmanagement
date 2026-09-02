"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  confirmBudgetBasis,
  fetchPlanning,
  fetchProjectByKey,
  fetchPspAnalysis,
  generatePlanningArtifact,
  generateJiraCsvFromPsp,
  generateBudgetPlanFromPsp,
  generateProjectIdea,
  savePlanningArtifact,
  saveProjectIdea,
  setPlanningArtifactStatus,
  updateBudgetBasis,
  updateProject,
  type LlmUsage,
  type PlanningState,
  type Project,
  type PspAnalysis,
} from "@/lib/api";
import { PLANNING_FLOW_STEPS, PLANNING_IDEA, type PlanningStepKey } from "@/lib/planning-steps";
import { usePlanningRealtime } from "@/hooks/usePlanningRealtime";

function formatLlmUsageMessage(usage: LlmUsage): string {
  const tokens = `${usage.input_tokens.toLocaleString()} in + ${usage.output_tokens.toLocaleString()} out (≈ ${usage.total_tokens.toLocaleString()} gesamt)`;
  if (usage.is_local) {
    return `KI lokal (${usage.model}): ${tokens} — keine API-Kosten`;
  }
  const cost = usage.estimated_cost_usd_display ?? "unbekannt";
  return `KI (${usage.provider}/${usage.model}): ${tokens} — geschätzt ${cost} API (nicht ChatGPT Plus / Claude Pro)`;
}

export function usePlanningPage(projectKey: string) {
  const [project, setProject] = useState<Project | null>(null);
  const [planning, setPlanning] = useState<PlanningState | null>(null);
  const [activeStep, setActiveStep] = useState<PlanningStepKey>(PLANNING_IDEA.key);
  const [draftContent, setDraftContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [llmMessage, setLlmMessage] = useState<string | null>(null);
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
    void load();
  }, [load]);

  usePlanningRealtime(projectKey, () => {
    void load();
  });

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

  const stepFilled = useCallback(
    (key: PlanningStepKey): boolean => {
      if (!planning) return false;
      if (key === PLANNING_IDEA.key) return planning.completion.has_project_idea;
      return planning.artifacts.find((a) => a.slug === key)?.has_content ?? false;
    },
    [planning]
  );

  const stepStatus = useCallback(
    (key: PlanningStepKey): string => {
      if (key === PLANNING_IDEA.key) {
        return planning?.completion.has_project_idea ? "draft" : "pending";
      }
      return planning?.artifacts.find((a) => a.slug === key)?.status ?? "pending";
    },
    [planning]
  );

  const persistContent = useCallback(async () => {
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
  }, [activeStep, draftContent, planning, projectKey]);

  const generateKi = useCallback(async () => {
    if (!planning) return;
    setGenerating(true);
    setError(null);
    setLlmMessage(null);
    try {
      const updated =
        activeStep === PLANNING_IDEA.key
          ? await generateProjectIdea(
              projectKey,
              planning.revision,
              draftContent.trim() || undefined
            )
          : await generatePlanningArtifact(projectKey, activeStep, planning.revision);
      setPlanning(updated);
      if (updated.llm_usage) {
        setLlmMessage(formatLlmUsageMessage(updated.llm_usage));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "KI-Generierung fehlgeschlagen");
    } finally {
      setGenerating(false);
    }
  }, [activeStep, draftContent, planning, projectKey]);

  const generateFromPsp = useCallback(async () => {
    if (!planning) return;
    setGenerating(true);
    setError(null);
    try {
      const updated =
        activeStep === "budgetplan"
          ? await generateBudgetPlanFromPsp(projectKey, planning.revision)
          : await generateJiraCsvFromPsp(projectKey, planning.revision);
      setPlanning(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generierung fehlgeschlagen");
    } finally {
      setGenerating(false);
    }
  }, [activeStep, planning, projectKey]);

  const setArtifactStatus = useCallback(
    async (status: "pending" | "draft" | "approved") => {
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
    },
    [activeStep, planning, projectKey]
  );

  const saveBudgetBasis = useCallback(async () => {
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
  }, [budgetCeiling, budgetNotes, planning, projectKey]);

  const confirmBudget = useCallback(async () => {
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
  }, [planning, projectKey]);

  const startNameEdit = useCallback(() => {
    if (!project) return;
    setNameDraft(project.name);
    setEditingName(true);
  }, [project]);

  const cancelNameEdit = useCallback(() => {
    setEditingName(false);
    setNameDraft("");
  }, []);

  const saveNameEdit = useCallback(async () => {
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
  }, [cancelNameEdit, nameDraft, project]);

  const savedContent =
    activeStep === PLANNING_IDEA.key
      ? planning?.project_idea ?? ""
      : planning?.artifacts.find((a) => a.slug === activeStep)?.content ?? "";

  return {
    project,
    planning,
    activeStep,
    setActiveStep,
    activeMeta,
    draftContent,
    setDraftContent,
    savedContent,
    error,
    llmMessage,
    saving,
    generating,
    loading,
    pspAnalysis,
    budgetCeiling,
    setBudgetCeiling,
    budgetNotes,
    setBudgetNotes,
    budgetLoading,
    editingName,
    nameDraft,
    setNameDraft,
    nameSaving,
    contentMode,
    setContentMode,
    showPreview,
    setShowPreview,
    stepFilled,
    stepStatus,
    persistContent,
    generateKi,
    generateFromPsp,
    setArtifactStatus,
    saveBudgetBasis,
    confirmBudget,
    startNameEdit,
    cancelNameEdit,
    saveNameEdit,
  };
}
