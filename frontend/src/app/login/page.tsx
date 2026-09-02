"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { APP_COPYRIGHT, APP_NAME } from "@/lib/appMeta";
import { InlineAlert } from "@/components/ui/inline-alert";
import { login, verify2fa } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = searchParams.get("from") || "/projects";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [needs2fa, setNeeds2fa] = useState(false);
  const [totpCode, setTotpCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(email, password);
      if (res.requires_2fa) {
        setNeeds2fa(true);
      } else {
        router.push(from);
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }

  async function on2fa(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await verify2fa(totpCode);
      router.push(from);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "2FA fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen app-page-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-3 shadow-md shadow-primary/25">
            <span className="text-primary-foreground font-bold text-xl">PM</span>
          </div>
          <h1 className="font-display text-2xl font-semibold text-foreground">{APP_NAME}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {needs2fa ? "Zwei-Faktor-Authentifizierung" : "Bitte melde dich an"}
          </p>
        </div>

        <div className="bg-card rounded-2xl shadow-card border border-border/80 p-6">
          {!needs2fa ? (
            <form onSubmit={onLogin} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">E-Mail</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Passwort</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
              </div>
              {error && <InlineAlert>{error}</InlineAlert>}
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Anmelden…" : "Anmelden"}
              </Button>
            </form>
          ) : (
            <form onSubmit={on2fa} className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Code aus der Authenticator-App eingeben:
              </p>
              <Input
                type="text"
                inputMode="numeric"
                required
                value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder="123456"
                autoComplete="one-time-code"
              />
              {error && <InlineAlert>{error}</InlineAlert>}
              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Prüfen…" : "Bestätigen"}
              </Button>
            </form>
          )}
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">{APP_COPYRIGHT}</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
