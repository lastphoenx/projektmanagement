"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, ArrowRight, Shield } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
          title="Systemstatus"
          description="Self-hosted Foundation — Auth, 2FA, verschlüsselte Projekte & Tasks"
          actions={
            <Button asChild>
              <Link href="/projects">
                Zu den Projekten
                <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          }
        />

        <div className="grid sm:grid-cols-2 gap-5">
          <Card className="stat-card border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-primary" />
                API
              </CardTitle>
              <CardDescription>Backend-Erreichbarkeit</CardDescription>
            </CardHeader>
            <CardContent>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              {health && (
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
              )}
              {!health && !error && (
                <p className="text-sm text-muted-foreground">Verbinde…</p>
              )}
            </CardContent>
          </Card>

          <Card className="stat-card border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-primary" />
                Sicherheit
              </CardTitle>
              <CardDescription>Phase 1–3 Foundation</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="text-sm space-y-1.5 text-muted-foreground">
                <li>Session-Login mit HttpOnly-Cookie</li>
                <li>TOTP 2FA + Recovery Codes</li>
                <li>Verschlüsselte Projekt- & Task-Daten</li>
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
