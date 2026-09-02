"use client";

import { useEffect, useState } from "react";
import { Download, Trash2 } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import {
  adminPrivacyErase,
  adminPrivacyExportUrl,
  adminPrivacyPurgeRetention,
  fetchAdminPrivacyUsers,
  type PrivacyUserSummary,
} from "@/lib/api";

export default function AdminPrivacyPage() {
  const [users, setUsers] = useState<PrivacyUserSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  async function load() {
    try {
      setUsers(await fetchAdminPrivacyUsers());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Laden fehlgeschlagen");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleErase(user: PrivacyUserSummary) {
    if (
      !window.confirm(
        `Benutzer ${user.id.slice(0, 8)}… wirklich pseudonymisieren/löschen? Nicht rückgängig machbar.`
      )
    ) {
      return;
    }
    setBusyId(user.id);
    setError(null);
    try {
      const result = await adminPrivacyErase(user.id);
      setMessage(
        `Benutzer pseudonymisiert (${result.audit_events_pseudonymized} Audit-Einträge angepasst).`
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Löschung fehlgeschlagen");
    } finally {
      setBusyId(null);
    }
  }

  async function handlePurge() {
    if (!window.confirm("Abgelaufene Sessions und alte Audit-Logs gemäss Retention löschen?")) {
      return;
    }
    setError(null);
    try {
      const result = await adminPrivacyPurgeRetention();
      setMessage(
        `Retention-Purge: ${result.purged.sessions} Sessions, ${result.purged.audit_log} Audit-Einträge.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Purge fehlgeschlagen");
    }
  }

  return (
    <AppLayout>
      <PageContainer width="wide">
        <PageHeader
          title="Datenschutz (DSGVO)"
          description="B.2 — Auskunft (Art. 15), Löschung/Pseudonymisierung (Art. 17), Retention-Purge."
          actions={
            <Button variant="outline" onClick={() => void handlePurge()}>
              Retention-Purge ausführen
            </Button>
          }
        />

        {error && <InlineAlert className="mb-4">{error}</InlineAlert>}
        {message && <InlineAlert variant="success" className="mb-4">{message}</InlineAlert>}

        <div className="rounded-xl border border-border/70 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-3">Benutzer-ID</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Rolle</th>
                <th className="text-left p-3">2FA</th>
                <th className="text-left p-3">Erstellt</th>
                <th className="text-right p-3">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-t border-border/60">
                  <td className="p-3 font-mono text-xs">{user.id}</td>
                  <td className="p-3">{user.is_active ? "aktiv" : "inaktiv"}</td>
                  <td className="p-3">{user.is_admin ? "Admin" : "Benutzer"}</td>
                  <td className="p-3">{user.totp_enabled ? "ja" : "nein"}</td>
                  <td className="p-3 text-muted-foreground">
                    {new Date(user.created_at).toLocaleDateString("de-CH")}
                  </td>
                  <td className="p-3">
                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(adminPrivacyExportUrl(user.id), "_blank")}
                      >
                        <Download className="w-4 h-4" />
                        Export
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="text-destructive border-destructive/30"
                        disabled={busyId === user.id || !user.is_active}
                        onClick={() => void handleErase(user)}
                      >
                        <Trash2 className="w-4 h-4" />
                        Löschen
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
