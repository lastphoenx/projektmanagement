"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { InlineAlert } from "@/components/ui/inline-alert";
import {
  fetchUserLlm,
  saveUserLlm,
  testUserLlm,
  type UserLlmState,
} from "@/lib/api";

function formatUsdPerMtok(value: number): string {
  return `$${value.toFixed(2)}`;
}

export default function UserLlmSettingsPage() {
  const [state, setState] = useState<UserLlmState | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserLlm()
      .then((s) => {
        setState(s);
        setProvider(s.active.provider);
        setModel(s.active.model);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Laden fehlgeschlagen"))
      .finally(() => setLoading(false));
  }, []);

  const providerMeta = state?.providers.find((p) => p.id === provider);
  const models = providerMeta?.models ?? [];
  const providerGuidance = state?.guidance.providers.find((p) => p.id === provider);

  useEffect(() => {
    if (models.length && !models.includes(model)) {
      setModel(models[0]);
    }
  }, [provider, models, model]);

  async function onSave() {
    setError(null);
    setMessage(null);
    try {
      const s = await saveUserLlm({ provider, model });
      setState(s);
      setMessage("KI-Einstellungen gespeichert.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  async function onTest() {
    setError(null);
    setMessage(null);
    try {
      const r = await testUserLlm({ provider, model });
      setMessage(r.message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test fehlgeschlagen");
    }
  }

  return (
    <AppLayout>
      <PageContainer width="medium">
        <PageHeader
          title="KI-Einstellungen"
          description="Wählen Sie Anbieter und Modell für die Planungs-KI. Zugangsdaten verwalten nur Betreiber in der Server-Konfiguration."
        />

        {loading ? (
          <p className="text-muted-foreground">Lade…</p>
        ) : (
          <div className="space-y-8">
            {error && <InlineAlert>{error}</InlineAlert>}
            {message && <InlineAlert variant="success">{message}</InlineAlert>}

            <section className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-6 space-y-4">
              <h2 className="font-semibold text-lg">{state?.guidance.controls.title}</h2>
              <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                {state?.guidance.controls.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>

              <div className="space-y-2 pt-2">
                <Label htmlFor="provider">Anbieter</Label>
                <select
                  id="provider"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  {state?.providers.map((p) => (
                    <option key={p.id} value={p.id} disabled={!p.configured}>
                      {p.label}
                      {p.configured ? "" : " — nicht verfügbar"}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model">Modell</Label>
                <select
                  id="model"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  disabled={!models.length}
                >
                  {models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={onSave} disabled={!providerMeta?.configured}>
                  Speichern
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={onTest}
                  disabled={!providerMeta?.configured}
                >
                  Verbindung testen
                </Button>
              </div>
            </section>

            {providerGuidance && (
              <section className="rounded-2xl border border-border/70 bg-card/60 p-6 space-y-3">
                <h2 className="font-semibold">Vor- und Nachteile — {providerMeta?.label}</h2>
                <div className="grid sm:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="font-medium text-emerald-700 dark:text-emerald-400 mb-1">Vorteile</p>
                    <ul className="list-disc pl-5 text-muted-foreground space-y-1">
                      {providerGuidance.pros.map((x) => (
                        <li key={x}>{x}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium text-amber-700 dark:text-amber-400 mb-1">Nachteile</p>
                    <ul className="list-disc pl-5 text-muted-foreground space-y-1">
                      {providerGuidance.cons.map((x) => (
                        <li key={x}>{x}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </section>
            )}

            <section className="rounded-2xl border border-border/70 bg-card/60 p-6 space-y-3">
              <h2 className="font-semibold">Modell-Empfehlungen</h2>
              {state?.guidance.ollama_filter_note && (
                <p className="text-xs text-muted-foreground">{state.guidance.ollama_filter_note}</p>
              )}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left border-b border-border/60">
                      <th className="py-2 pr-4">Einsatz</th>
                      <th className="py-2 pr-4">Ollama</th>
                      <th className="py-2 pr-4">OpenAI</th>
                      <th className="py-2">Anthropic</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state?.guidance.model_hints.map((row) => (
                      <tr key={row.use_case} className="border-b border-border/40">
                        <td className="py-2 pr-4 font-medium">{row.use_case}</td>
                        <td className="py-2 pr-4 text-muted-foreground">{row.ollama}</td>
                        <td className="py-2 pr-4 text-muted-foreground">{row.openai}</td>
                        <td className="py-2 text-muted-foreground">{row.anthropic}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-amber-500/40 bg-amber-500/5 p-6 space-y-4">
              <h2 className="font-semibold">{state?.billing_note.title}</h2>
              {state?.billing_note.paragraphs.map((p) => (
                <p key={p.slice(0, 40)} className="text-sm text-muted-foreground">
                  {p}
                </p>
              ))}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left border-b border-border/60">
                      <th className="py-2 pr-4">Abo</th>
                      <th className="py-2 pr-4">Enthält</th>
                      <th className="py-2">Nicht enthalten</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state?.billing_note.products.map((row) => (
                      <tr key={row.name} className="border-b border-border/40">
                        <td className="py-2 pr-4 font-medium">{row.name}</td>
                        <td className="py-2 pr-4 text-muted-foreground">{row.covers}</td>
                        <td className="py-2 text-muted-foreground">{row.not_covers}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-border/70 bg-card/60 p-6 space-y-3">
              <h2 className="font-semibold">API-Preise (Pay-as-you-go, USD / 1M Token)</h2>
              <p className="text-xs text-muted-foreground">
                Grobe Schätzung — tatsächliche Abrechnung über OpenAI Platform bzw. Anthropic Console.
                Spalte «Idee» ≈ typischer Projektidee-Aufruf (
                {state?.typical_planning_tokens.project_idea.input.toLocaleString()} in /
                {" "}
                {state?.typical_planning_tokens.project_idea.output.toLocaleString()} out Token).
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left border-b border-border/60">
                      <th className="py-2 pr-4">Modell</th>
                      <th className="py-2 pr-4">Input</th>
                      <th className="py-2 pr-4">Output</th>
                      <th className="py-2">≈ Idee</th>
                    </tr>
                  </thead>
                  <tbody>
                    {state?.pricing_catalog.map((row) => (
                      <tr key={row.model} className="border-b border-border/40">
                        <td className="py-2 pr-4 font-medium">{row.model}</td>
                        <td className="py-2 pr-4 text-muted-foreground">
                          {formatUsdPerMtok(row.input_usd_per_mtok)}/M
                        </td>
                        <td className="py-2 pr-4 text-muted-foreground">
                          {formatUsdPerMtok(row.output_usd_per_mtok)}/M
                        </td>
                        <td className="py-2 text-muted-foreground">
                          ${row.example_idea_usd.toFixed(4)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="rounded-2xl border border-primary/30 bg-primary/5 p-6 space-y-3">
              <h2 className="font-semibold">{state?.guidance.privacy.title}</h2>
              <ul className="list-disc pl-5 text-sm text-muted-foreground space-y-1">
                {state?.guidance.privacy.rules.map((rule) => (
                  <li key={rule}>{rule}</li>
                ))}
              </ul>
              <p className="text-xs text-muted-foreground">{state?.guidance.privacy.note}</p>
            </section>
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}
