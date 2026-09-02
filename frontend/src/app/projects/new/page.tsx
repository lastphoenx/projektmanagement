"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { BackLink } from "@/components/layout/BackLink";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { WizardStepIndicator } from "@/components/wizard/WizardStepIndicator";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
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
        <BackLink href="/projects">Projekte</BackLink>

        <PageHeader
          title="Neues Projekt"
          description="Projekttyp wählen, Key und Name festlegen — danach startest du mit den Planungsschritten."
        />

        <WizardStepIndicator steps={STEPS} currentStep={step} />

        {error && <InlineAlert className="mb-6">{error}</InlineAlert>}

        {step === 0 && (
          <section className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-6 space-y-4">
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
                      ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                      : "border-border/70 hover:border-primary/30 hover:bg-muted/30"
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
                className="planning-editor-field w-full min-h-[5rem]"
                placeholder="Kurzbeschreibung…"
              />
            </div>
            <div className="flex flex-wrap gap-2">
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
          <form
            onSubmit={onSubmit}
            className="space-y-5 rounded-2xl border border-border/70 bg-card/80 shadow-card p-6"
          >
            <dl className="space-y-3 text-sm rounded-xl border border-border/70 bg-muted/20 p-4">
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
            <div className="flex flex-wrap gap-2">
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
