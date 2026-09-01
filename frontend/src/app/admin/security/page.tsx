"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { fetchAdminSecurityCatalog, type SecurityCatalogState } from "@/lib/api";

export default function AdminSecurityPage() {
  const [catalog, setCatalog] = useState<SecurityCatalogState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAdminSecurityCatalog()
      .then(setCatalog)
      .catch((e) => setError(e instanceof Error ? e.message : "Fehler"));
  }, []);

  return (
    <AppLayout>
      <PageContainer width="wide">
        <PageHeader
          title="Sicherheitskatalog"
          description="B.1 — Zwei-Ebenen-Modell: Schutzklassen-Katalog + Tabellen-Defaults + Feld-Overrides (nur Lesen)."
        />
        {error && <p className="text-destructive text-sm mb-4">{error}</p>}
        {catalog && (
          <div className="space-y-8">
            <section className="rounded-xl border border-border/70 bg-muted/20 p-4 text-sm space-y-2">
              <h2 className="font-display font-semibold">Konzept (3 Ebenen)</h2>
              <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                <li>
                  <span className="text-foreground">Ebene 1 — Schutzklassen:</span>{" "}
                  {catalog.concept.level_1}
                </li>
                <li>
                  <span className="text-foreground">Ebene 2 — Tabellen-Default:</span>{" "}
                  {catalog.concept.level_2}
                </li>
                <li>
                  <span className="text-foreground">Ebene 3 — Feld-Override:</span>{" "}
                  {catalog.concept.level_3}
                </li>
              </ol>
            </section>

            <section>
              <h2 className="font-display text-lg font-semibold mb-1">Ebene 1: Schutzklassen</h2>
              <p className="text-sm text-muted-foreground mb-3">
                Gilt für alle Felder einer Klasse — Retention, DSGVO, LLM-Gate, Löschstrategie.
              </p>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-2">Klasse</th>
                      <th className="text-left p-2">Retention</th>
                      <th className="text-left p-2">DSGVO</th>
                      <th className="text-left p-2">LLM extern</th>
                      <th className="text-left p-2">Löschung</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.classification_catalog.map((c) => (
                      <tr key={c.name} className="border-t border-border/50">
                        <td className="p-2 font-mono">{c.name}</td>
                        <td className="p-2">{c.retention_days ?? "—"}</td>
                        <td className="p-2">{c.gdpr_relevant ? "ja" : "nein"}</td>
                        <td className="p-2">
                          {c.never_leaves_infrastructure
                            ? "blockiert"
                            : c.requires_anonymization_before_external_llm
                              ? "anonymisieren"
                              : "frei"}
                        </td>
                        <td className="p-2">{c.erasure_strategy}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-semibold mb-1">Ebene 2: Tabellen-Defaults</h2>
              <p className="text-sm text-muted-foreground mb-3">
                Jede Tabelle hat eine <code className="text-xs">classification</code>-Spalte als
                Fallback, wenn kein Feld-Override greift.
              </p>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-2">Modell</th>
                      <th className="text-left p-2">Tabelle</th>
                      <th className="text-left p-2">Default-Klasse</th>
                      <th className="text-left p-2">Quelle</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.table_defaults.map((t) => (
                      <tr key={t.model} className="border-t border-border/50">
                        <td className="p-2 font-mono">{t.model}</td>
                        <td className="p-2 font-mono text-xs">{t.table}</td>
                        <td className="p-2 font-mono">{t.default_classification}</td>
                        <td className="p-2 text-muted-foreground text-xs">{t.policy_source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-semibold mb-1">
                Planungsschritte → Datenbankfelder
              </h2>
              <p className="text-sm text-muted-foreground mb-3">
                Jeder Planungsschritt speichert Markdown in einem verschlüsselten Feld. Die
                effektive Klasse kommt aus Tabellen-Default + Feld-Registry.
              </p>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-2">Schritt</th>
                      <th className="text-left p-2">Slug</th>
                      <th className="text-left p-2">Feld</th>
                      <th className="text-left p-2">Tabellen-Default</th>
                      <th className="text-left p-2">Effektiv</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.planning_step_fields.map((s) => (
                      <tr
                        key={`${s.slug ?? "idea"}-${s.field}`}
                        className="border-t border-border/50"
                      >
                        <td className="p-2">
                          {s.label}
                          {"note" in s && s.note ? (
                            <span className="block text-xs text-muted-foreground">{s.note}</span>
                          ) : null}
                        </td>
                        <td className="p-2 font-mono text-xs">{s.slug ?? "—"}</td>
                        <td className="p-2 font-mono text-xs">
                          {s.model}.{s.field}
                        </td>
                        <td className="p-2 font-mono">{s.table_default}</td>
                        <td className="p-2 font-mono">
                          {s.effective_classification}
                          {s.has_field_override ? (
                            <span className="ml-1 text-xs text-amber-700">(Override)</span>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section>
              <h2 className="font-display text-lg font-semibold mb-1">Ebene 3: Feld-Registry (Overrides)</h2>
              <p className="text-sm text-muted-foreground mb-3">
                Nur explizite Abweichungen vom Tabellen-Default — Code-Mapping in{" "}
                <code className="text-xs">field_registry.py</code>.
              </p>
              <div className="overflow-x-auto rounded-xl border border-border/70">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="text-left p-2">Feld</th>
                      <th className="text-left p-2">Tabellen-Default</th>
                      <th className="text-left p-2">Override</th>
                      <th className="text-left p-2">DSGVO personenbezogen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog.field_registry_overrides.map((f) => (
                      <tr key={`${f.model}.${f.field}`} className="border-t border-border/50">
                        <td className="p-2 font-mono text-xs">
                          {f.model}.{f.field}
                        </td>
                        <td className="p-2 font-mono">{f.table_default}</td>
                        <td className="p-2 font-mono">
                          {f.is_override ? (
                            <span className="text-amber-700">{f.classification}</span>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="p-2">{f.gdpr_personal ? "ja" : "nein"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}
