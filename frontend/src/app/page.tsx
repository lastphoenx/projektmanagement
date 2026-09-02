"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, ClipboardList, Shield } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { InlineAlert } from "@/components/ui/inline-alert";
import { fetchHealth, type HealthResponse } from "@/lib/api";

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <AppLayout>
      <PageContainer width="medium">
        <PageHeader
          title="Übersicht"
          description="Projektmanagement mit KI-Planungskern, verschlüsselter Speicherung und RBAC."
          actions={
            <Button asChild>
              <Link href="/projects">
                Zu den Projekten
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          }
        />

        {error && <InlineAlert className="mb-6">{error}</InlineAlert>}

        <div className="grid sm:grid-cols-2 gap-5">
          <Card className="stat-card rounded-2xl border-border/70 shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-display">
                <Activity className="w-5 h-5 text-primary" />
                API
              </CardTitle>
              <CardDescription>Backend-Erreichbarkeit</CardDescription>
            </CardHeader>
            <CardContent>
              {health ? (
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">Status</dt>
                    <dd className="font-medium">{health.status}</dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-muted-foreground">Tenant</dt>
                    <dd className="font-medium">{health.tenant}</dd>
                  </div>
                </dl>
              ) : !error ? (
                <p className="text-sm text-muted-foreground">Verbinde…</p>
              ) : null}
            </CardContent>
          </Card>

          <Card className="stat-card rounded-2xl border-border/70 shadow-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-display">
                <ClipboardList className="w-5 h-5 text-primary" />
                Planungskern
              </CardTitle>
              <CardDescription>Projektidee + 10 Planungsschritte</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-1.5 text-muted-foreground">
                <li>KI für Idee und Schritte 1–6, 9–10</li>
                <li>Jira CSV & Budgetplan aus PSP</li>
                <li>Vollständigkeits-Indikator pro Projekt</li>
              </ul>
              <Button variant="outline" size="sm" className="mt-4" asChild>
                <Link href="/projects/new">Neues Projekt anlegen</Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="stat-card rounded-2xl border-border/70 shadow-card sm:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-display">
                <Shield className="w-5 h-5 text-primary" />
                Sicherheit
              </CardTitle>
              <CardDescription>Verschlüsselung, Auth & Klassifizierung</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-1.5 text-muted-foreground sm:columns-2 sm:gap-8">
                <li>Session-Login mit HttpOnly-Cookie</li>
                <li>TOTP 2FA + Recovery Codes</li>
                <li>Verschlüsselte Projekt- & Planungsdaten</li>
                <li>RBAC mit Soft-Locking</li>
              </ul>
              <Button variant="outline" size="sm" className="mt-4" asChild>
                <Link href="/login">Anmelden</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </PageContainer>
    </AppLayout>
  );
}
