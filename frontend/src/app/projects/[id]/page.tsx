"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import {
  createTask,
  fetchProject,
  fetchTasks,
  lockTask,
  type Project,
  type Task,
  unlockTask,
  updateTask,
} from "@/lib/api";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  useEffect(() => {
    if (!projectId) return;
    fetchProject(projectId).then(setProject).catch(() => setError("Projekt nicht gefunden"));
    fetchTasks(projectId).then(setTasks).catch(() => {});
  }, [projectId]);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      const t = await createTask(projectId, title.trim());
      setTasks((prev) => [t, ...prev]);
      setTitle("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fehler");
    }
  }

  async function startEdit(task: Task) {
    try {
      const locked = await lockTask(projectId, task.id);
      setTasks((prev) => prev.map((t) => (t.id === task.id ? locked : t)));
      setEditingId(task.id);
      setEditTitle(task.title);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lock fehlgeschlagen");
    }
  }

  async function saveEdit(task: Task) {
    try {
      const updated = await updateTask(projectId, task.id, {
        title: editTitle,
        version: task.version,
      });
      setTasks((prev) => prev.map((t) => (t.id === task.id ? updated : t)));
      await unlockTask(projectId, task.id);
      setEditingId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speichern fehlgeschlagen");
    }
  }

  if (error && !project) {
    return (
      <main style={{ maxWidth: 720, margin: "3rem auto", padding: "0 1.5rem" }}>
        <p>{error}</p>
        <Link href="/projects">Zurück</Link>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 720, margin: "3rem auto", padding: "0 1.5rem" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "2rem",
        }}
      >
        <div>
          <Link href="/projects" style={{ fontSize: "0.875rem" }}>
            ← Projekte
          </Link>
          <h1 style={{ margin: "0.5rem 0 0" }}>{project?.name ?? "…"}</h1>
          {project?.description && (
            <p style={{ color: "var(--muted)", margin: "0.5rem 0 0" }}>{project.description}</p>
          )}
        </div>
        <ThemeToggle />
      </header>

      {error && <p style={{ color: "#ef4444" }}>{error}</p>}

      <h2 style={{ fontSize: "1.125rem" }}>Tasks</h2>
      <form onSubmit={onCreate} style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Neuer Task…"
          style={{ flex: 1, padding: 8 }}
        />
        <button type="submit">Hinzufügen</button>
      </form>

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {tasks.map((task) => (
          <li
            key={task.id}
            style={{
              background: "var(--card)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "1rem",
              marginBottom: "0.75rem",
            }}
          >
            {editingId === task.id ? (
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  style={{ flex: 1, padding: 8 }}
                />
                <button type="button" onClick={() => saveEdit(task)}>
                  Speichern
                </button>
              </div>
            ) : (
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{task.title}</strong>
                  <span style={{ marginLeft: 8, color: "var(--muted)", fontSize: "0.75rem" }}>
                    {task.status}
                    {task.locked_by_id ? " · 🔒" : ""}
                  </span>
                </div>
                <button type="button" onClick={() => startEdit(task)}>
                  Bearbeiten
                </button>
              </div>
            )}
          </li>
        ))}
        {tasks.length === 0 && <p style={{ color: "var(--muted)" }}>Noch keine Tasks.</p>}
      </ul>
    </main>
  );
}
