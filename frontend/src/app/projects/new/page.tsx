"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createProject } from "@/lib/api";
import {
  WIZARD_PROJECT_TYPE_LABELS,
  WIZARD_PROJECT_TYPES,
  type WizardProjectType,
} from "@/lib/project-types";
import { cn } from "@/lib/utils";

const STEPS = ["Typ", "Details", "Fertig"] as const;

export default function NewProjectPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [projectType, setProjectType] = useState<WizardProjectType>("other");
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function normalizeKey(value: string) {
    return value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!key.trim() || !name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const project = await createProject({
        key: key.trim(),
        name: name.trim(),
        project_type: projectType,
        description: description.trim() || undefined,
      });
      router.push(`/projects/${project.key}/planung`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler beim Anlegen");
      setSubmitting(false);
    }
  }

  return (
    <AppLayout>
      <PageContainer width="narrow">
        <Link
          href="/projects"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Projekte
        </Link>

        <PageHeader
          title="Neues Projekt"
          description="Projekttyp wählen, Key und Name festlegen — danach startest du mit den Planungsschritten."
        />

        <div className="flex gap-2 mb-8">
          {STEPS.map((label, index) => (
            <div
              key={label}
              className={cn(
                "flex-1 rounded-lg border px-3 py-2 text-center text-xs font-medium",
                index === step
                  ? "border-primary bg-primary/10 text-primary"
                  : index < step
                    ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
                    : "border-border/70 text-muted-foreground"
              )}
            >
              {index < step ? <Check className="w-3 h-3 inline mr-1" /> : null}
              {index + 1}. {label}
            </div>
          ))}
        </div>

        {error && (
          <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2 mb-6">
            {error}
          </p>
        )}

        {step === 0 && (
          <section className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Kategorie für die Einordnung — die Planungsschritte sind für alle Typen gleich.
            </p>
            <div className="grid gap-3">
              {WIZARD_PROJECT_TYPES.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setProjectType(type)}
                  className={cn(
                    "rounded-xl border p-4 text-left transition-colors",
                    projectType === type
                      ? "border-primary bg-primary/5"
                      : "border-border/70 hover:border-primary/30"
                  )}
                >
                  <p className="font-medium">{WIZARD_PROJECT_TYPE_LABELS[type]}</p>
                </button>
              ))}
            </div>
            <Button type="button" onClick={() => setStep(1)} className="w-full sm:w-auto">
              Weiter
              <ArrowRight className="w-4 h-4" />
            </Button>
          </section>
        )}

        {step === 1 && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (key.trim().length >= 2 && name.trim()) setStep(2);
            }}
            className="space-y-5 rounded-2xl border border-border/70 bg-card/80 shadow-card p-6"
          >
            <div className="space-y-2">
              <Label htmlFor="key">Projekt-Key</Label>
              <Input
                id="key"
                value={key}
                onChange={(e) => setKey(normalizeKey(e.target.value))}
                placeholder="z. B. OTR"
                className="font-mono uppercase"
                maxLength={8}
                required
              />
              <p className="text-xs text-muted-foreground">
                2–8 Zeichen, beginnt mit Buchstabe (A–Z, 0–9).
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Projektname</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Name des Projekts"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Beschreibung (optional)</Label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Kurzbeschreibung…"
              />
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep(0)}>
                Zurück
              </Button>
              <Button type="submit">
                Weiter
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={onSubmit} className="space-y-5 rounded-2xl border border-border/70 bg-card/80 shadow-card p-6">
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-muted-foreground">Typ</dt>
                <dd className="font-medium">{WIZARD_PROJECT_TYPE_LABELS[projectType]}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted-foreground">Key</dt>
                <dd className="font-mono font-medium">{key}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted-foreground">Name</dt>
                <dd className="font-medium text-right">{name}</dd>
              </div>
            </dl>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => setStep(1)}>
                Zurück
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Wird angelegt…" : "Projekt anlegen & Planung starten"}
              </Button>
            </div>
          </form>
        )}
      </PageContainer>
    </AppLayout>
  );
}
