"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  fetchAdminLlm,
  saveAdminLlm,
  testAdminLlm,
  type AdminLlmState,
} from "@/lib/api";

export default function AdminLlmPage() {
  const [state, setState] = useState<AdminLlmState | null>(null);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminLlm()
      .then((s) => {
        setState(s);
        setProvider(s.active.provider);
        setModel(s.active.model);
        setBaseUrl(s.active.base_url ?? "");
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Laden fehlgeschlagen"))
      .finally(() => setLoading(false));
  }, []);

  const providerMeta = state?.providers.find((p) => p.id === provider);
  const models = providerMeta?.models ?? [];

  useEffect(() => {
    if (models.length && !models.includes(model)) {
      setModel(models[0]);
    }
  }, [provider, models, model]);

  async function onSave() {
    setError(null);
    setMessage(null);
    try {
      const s = await saveAdminLlm({
        provider,
        model,
        base_url: baseUrl || undefined,
        api_key: apiKey || undefined,
      });
      setState(s);
      setApiKey("");
      setMessage("KI-Einstellungen gespeichert.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Speichern fehlgeschlagen");
    }
  }

  async function onTest() {
    setError(null);
    setMessage(null);
    try {
      const r = await testAdminLlm({ provider, model, base_url: baseUrl || undefined });
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
          description="Provider und Modell für die Planungs-KI. API-Keys können in .env oder hier hinterlegt werden (verschlüsselt)."
        />
        {loading ? (
          <p className="text-muted-foreground">Lade…</p>
        ) : (
          <div className="space-y-6 rounded-2xl border border-border/70 bg-card/80 shadow-card p-6">
            {error && <p className="text-sm text-destructive">{error}</p>}
            {message && <p className="text-sm text-emerald-700">{message}</p>}

            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <select
                id="provider"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                {state?.providers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label} {p.configured ? "✓" : "— nicht erreichbar"}
                  </option>
                ))}
              </select>
            </div>

            {provider === "ollama" && (
              <div className="space-y-2">
                <Label htmlFor="baseUrl">Ollama-URL</Label>
                <Input
                  id="baseUrl"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="http://192.168.131.60:11434"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="model">Modell</Label>
              <select
                id="model"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                {models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {provider !== "ollama" && (
              <div className="space-y-2">
                <Label htmlFor="apiKey">API-Key (optional, überschreibt .env)</Label>
                <Input
                  id="apiKey"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Leer lassen = aus .env"
                />
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Button type="button" onClick={onSave}>
                Speichern
              </Button>
              <Button type="button" variant="outline" onClick={onTest}>
                Verbindung testen
              </Button>
            </div>
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}
