"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Circle, Loader2, Lock, Pencil } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

const STATUS_LABELS: Record<string, string> = {
  open: "Offen",
  in_progress: "In Arbeit",
  done: "Erledigt",
};

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
      <AppLayout>
        <PageContainer width="narrow">
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button variant="outline" asChild>
            <Link href="/projects">
              <ArrowLeft className="w-4 h-4" />
              Zurück
            </Link>
          </Button>
        </PageContainer>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageContainer>
        <div className="mb-8">
          <Link
            href="/projects"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Projekte
          </Link>
          <h1 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight">
            {project?.name ?? "…"}
          </h1>
          {project?.description && (
            <p className="text-sm text-muted-foreground mt-1.5 max-w-2xl">{project.description}</p>
          )}
        </div>

        {error && (
          <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2 mb-6">
            {error}
          </p>
        )}

        <section>
          <h2 className="font-display text-lg font-semibold mb-4">Tasks</h2>

          <form
            onSubmit={onCreate}
            className="flex flex-col sm:flex-row gap-2 mb-6 rounded-2xl border border-border/70 bg-card/80 shadow-card p-4"
          >
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Neuer Task…"
              className="flex-1"
            />
            <Button type="submit" className="shrink-0">
              Hinzufügen
            </Button>
          </form>

          {tasks.length === 0 ? (
            <p className="text-muted-foreground text-center py-8 rounded-2xl border border-dashed border-border/70">
              Noch keine Tasks.
            </p>
          ) : (
            <ul className="space-y-3">
              {tasks.map((task) => (
                <li
                  key={task.id}
                  className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-4 stat-card"
                >
                  {editingId === task.id ? (
                    <div className="flex flex-col sm:flex-row gap-2">
                      <Input
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        className="flex-1"
                      />
                      <Button type="button" onClick={() => saveEdit(task)}>
                        Speichern
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0">
                        <StatusIcon status={task.status} />
                        <div className="min-w-0">
                          <p className="font-medium truncate">{task.title}</p>
                          <div className="flex flex-wrap items-center gap-2 mt-1">
                            <span className="text-xs rounded-full px-2 py-0.5 bg-muted text-muted-foreground">
                              {STATUS_LABELS[task.status] ?? task.status}
                            </span>
                            {task.locked_by_id && (
                              <span className="inline-flex items-center gap-1 text-xs text-amber-600">
                                <Lock className="w-3 h-3" />
                                Gesperrt
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => startEdit(task)}
                        className="shrink-0"
                      >
                        <Pencil className="w-4 h-4" />
                        Bearbeiten
                      </Button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </PageContainer>
    </AppLayout>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "done") {
    return <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />;
  }
  if (status === "in_progress") {
    return <Loader2 className="w-5 h-5 text-primary shrink-0 mt-0.5" />;
  }
  return <Circle className="w-5 h-5 text-muted-foreground shrink-0 mt-0.5" />;
}
