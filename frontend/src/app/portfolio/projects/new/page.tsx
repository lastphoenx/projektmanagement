"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { AlertTriangle, FolderOpen, Save } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { BackLink } from "@/components/layout/BackLink";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioProjectForm } from "@/components/portfolio/PortfolioProjectForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import {
  createPortfolioProject,
  fetchPortfolioEligibleProjects,
  type PortfolioEligibleProject,
} from "@/lib/api";
import { INITIAL_PORTFOLIO_FORM, type PortfolioFormData } from "@/lib/portfolio-types";

export default function NewPortfolioProjectPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<PortfolioFormData>(INITIAL_PORTFOLIO_FORM);
  const [eligible, setEligible] = useState<PortfolioEligibleProject[]>([]);
  const [selectedKey, setSelectedKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selected = eligible.find((p) => p.project_key === selectedKey);

  useEffect(() => {
    fetchPortfolioEligibleProjects()
      .then(setEligible)
      .catch(() => setEligible([]));
  }, []);

  function handleProjectSelect(event: ChangeEvent<HTMLSelectElement>) {
    const key = event.target.value;
    setSelectedKey(key);
    const found = eligible.find((p) => p.project_key === key);
    if (found) {
      setFormData((prev) => ({ ...prev, name: found.name }));
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!formData.name.trim()) {
      setError("Projektname ist erforderlich.");
      return;
    }
    if (!selectedKey) {
      setError("Bitte ein Projekt verknüpfen.");
      return;
    }
    if (selected && !selected.is_complete) {
      setError(
        `Planung unvollständig (${selected.filled_count}/${selected.total_count}). Portfolio-Aufnahme erst nach vollständiger Planung möglich.`
      );
      return;
    }
    if (selected && !selected.can_manage) {
      setError("Keine Berechtigung für dieses Projekt.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const created = await createPortfolioProject({ ...formData, project_key: selectedKey });
      router.push(`/portfolio/projects/${created.id}/edit`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppLayout>
      <PageContainer>
        <BackLink href="/portfolio">Zurück zum Portfolio</BackLink>
        <PageHeader
          title="Neues Portfolio-Projekt"
          description="Projekt bewerten und in die Portfolio-Matrix aufnehmen. Voraussetzung: vollständige Planung."
        />

        {eligible.length > 0 && (
          <Card className="mb-6 border-blue-200 bg-blue-50/80">
            <CardContent className="pt-5">
              <div className="flex items-start gap-3">
                <FolderOpen className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
                <div className="flex-1 space-y-3">
                  <p className="text-sm font-medium text-blue-900">PM-Projekt verknüpfen</p>
                  <select
                    value={selectedKey}
                    onChange={handleProjectSelect}
                    className="w-full max-w-md border border-blue-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">— Projekt auswählen —</option>
                    {eligible.map((p) => (
                      <option key={p.project_key} value={p.project_key} disabled={!p.can_manage}>
                        [{p.project_key}] {p.name}
                        {!p.is_complete ? ` — Planung ${p.filled_count}/${p.total_count}` : ""}
                      </option>
                    ))}
                  </select>
                  {selected && !selected.is_complete && (
                    <div className="text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                      <p className="font-medium flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Planung unvollständig ({selected.filled_count}/{selected.total_count})
                      </p>
                      {selected.missing_labels.length > 0 && (
                        <p className="mt-1">Fehlend: {selected.missing_labels.join(", ")}</p>
                      )}
                      <Link
                        href={`/projects/${selected.project_key}/planung`}
                        className="underline font-medium mt-1 inline-block"
                      >
                        Zur Planung →
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <InlineAlert variant="error">{error}</InlineAlert>}

          <PortfolioProjectForm formData={formData} onChange={setFormData} />

          <div className="flex flex-wrap gap-3">
            <Button
              type="submit"
              disabled={
                saving ||
                !selectedKey ||
                (selected != null && (!selected.is_complete || !selected.can_manage))
              }
            >
              <Save className="w-4 h-4" />
              {saving ? "Wird gespeichert…" : "Projekt bewerten & speichern"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link href="/portfolio">Abbrechen</Link>
            </Button>
          </div>
        </form>
      </PageContainer>
    </AppLayout>
  );
}
