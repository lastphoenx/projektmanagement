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
          description="Klassifizierungs-Regeln (B.1) und Feld-Overrides — nur Lesen, Änderungen per Code-Review."
        />
        {error && <p className="text-destructive text-sm mb-4">{error}</p>}
        {catalog && (
          <div className="space-y-8">
            <section>
              <h2 className="font-display text-lg font-semibold mb-3">Schutzklassen</h2>
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
              <h2 className="font-display text-lg font-semibold mb-3">Feld-Registry (Overrides)</h2>
              <ul className="text-sm space-y-1">
                {catalog.field_registry_overrides.map((f) => (
                  <li key={`${f.model}.${f.field}`} className="font-mono text-xs">
                    {f.model}.{f.field} → {f.classification}
                    {f.gdpr_personal ? " (personenbezogen)" : ""}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}
