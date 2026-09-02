"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Save, Trash2 } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { BackLink } from "@/components/layout/BackLink";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { PortfolioProjectForm } from "@/components/portfolio/PortfolioProjectForm";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import {
  deletePortfolioProject,
  fetchPortfolioProject,
  updatePortfolioProject,
} from "@/lib/api";
import { portfolioToFormData, type PortfolioFormData } from "@/lib/portfolio-types";
import { tierColorClass, tierLabel } from "@/lib/portfolio-metrics";

export default function EditPortfolioProjectPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params.id;

  const [formData, setFormData] = useState<PortfolioFormData | null>(null);
  const [projectKey, setProjectKey] = useState<string | null>(null);
  const [tier, setTier] = useState<string | null>(null);
  const [wsjf, setWsjf] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    fetchPortfolioProject(id)
      .then((entry) => {
        setFormData(portfolioToFormData(entry));
        setProjectKey(entry.project_key);
        setTier(entry.tier);
        setWsjf(entry.wsjf);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Laden fehlgeschlagen"))
      .finally(() => setLoading(false));
  }, [id]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!formData || !id) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updatePortfolioProject(id, formData);
      setTier(updated.tier);
      setWsjf(updated.wsjf);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!id || !window.confirm("Portfolio-Eintrag wirklich löschen?")) return;
    setDeleting(true);
    try {
      await deletePortfolioProject(id);
      router.push("/portfolio");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Löschen fehlgeschlagen");
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <PageContainer>
          <p className="text-muted-foreground py-16 text-center">Wird geladen…</p>
        </PageContainer>
      </AppLayout>
    );
  }

  if (!formData) {
    return (
      <AppLayout>
        <PageContainer>
          <InlineAlert variant="error">{error ?? "Eintrag nicht gefunden"}</InlineAlert>
        </PageContainer>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageContainer>
        <BackLink href="/portfolio">Zurück zum Portfolio</BackLink>
        <PageHeader
          title={formData.name}
          description={
            <>
              {projectKey && (
                <>
                  Projekt{" "}
                  <Link href={`/projects/${projectKey}/planung`} className="text-primary underline">
                    {projectKey}
                  </Link>
                  {" · "}
                </>
              )}
              {tier && (
                <span className={`inline-flex text-xs px-2 py-0.5 rounded border ${tierColorClass(tier)}`}>
                  {tierLabel(tier)}
                </span>
              )}
              {wsjf != null && (
                <span className="text-muted-foreground ml-2">WSJF {wsjf.toFixed(2)}</span>
              )}
            </>
          }
        />

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <InlineAlert variant="error">{error}</InlineAlert>}

          <PortfolioProjectForm formData={formData} onChange={setFormData} />

          <div className="flex flex-wrap gap-3">
            <Button type="submit" disabled={saving}>
              <Save className="w-4 h-4" />
              {saving ? "Wird gespeichert…" : "Änderungen speichern"}
            </Button>
            <Button type="button" variant="outline" asChild>
              <Link href="/portfolio">Zurück</Link>
            </Button>
            <Button
              type="button"
              variant="outline"
              className="text-destructive border-destructive/30 hover:bg-destructive/10"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? "Wird gelöscht…" : "Aus Portfolio entfernen"}
            </Button>
          </div>
        </form>
      </PageContainer>
    </AppLayout>
  );
}
