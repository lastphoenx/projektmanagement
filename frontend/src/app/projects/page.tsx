"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { createProject, fetchMe, fetchProjects, logout, type Project, type User } from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function ProjectsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => setError("Nicht angemeldet"));
    fetchProjects()
      .then(setProjects)
      .catch(() => {});
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const p = await createProject(name.trim());
      setProjects((prev) => [p, ...prev]);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler");
    }
  }

  async function onLogout() {
    await logout();
    window.location.href = "/login";
  }

  if (error && !user) {
    return (
      <main style={{ maxWidth: 640, margin: "4rem auto", padding: "0 1.5rem" }}>
        <p>{error}</p>
        <Link href="/login">Zum Login</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 720, margin: "3rem auto", padding: "0 1.5rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <div>
          <h1 style={{ margin: 0 }}>Projekte</h1>
          {user && (
            <p style={{ margin: "0.25rem 0 0", color: "var(--muted)", fontSize: "0.875rem" }}>
              {user.is_admin ? "Admin" : "Benutzer"} · 2FA: {user.totp_enabled ? "aktiv" : "aus"}
            </p>
          )}
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <ThemeToggle />
          <button type="button" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <form onSubmit={onCreate} style={{ display: "flex", gap: "0.5rem", marginBottom: "2rem" }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Neues Projekt…"
          style={{ flex: 1, padding: 8 }}
        />
        <button type="submit">Anlegen</button>
      </form>

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {projects.map((p) => (
          <li
            key={p.id}
            style={{
              background: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "1rem",
              marginBottom: "0.75rem",
            }}
          >
            <strong>
              <Link href={`/projects/${p.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                {p.name}
              </Link>
            </strong>
            {p.description && (
              <p style={{ margin: "0.5rem 0 0", color: "var(--muted)" }}>{p.description}</p>
            )}
          </li>
        ))}
        {projects.length === 0 && <p style={{ color: "var(--muted)" }}>Noch keine Projekte.</p>}
      </ul>
    </main>
  );
}
