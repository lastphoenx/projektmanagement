"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { ChevronRight, Clock, FolderKanban, Plus } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { PageContainer } from "@/components/layout/PageContainer";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { fetchMe, fetchProjects, type Project, type User } from "@/lib/api";
import { WIZARD_PROJECT_TYPE_LABELS, type WizardProjectType } from "@/lib/project-types";
import { cn } from "@/lib/utils";

export default function ProjectsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => setError("auth"));
    fetchProjects()
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (error === "auth" && !user) {
    return (
      <div className="min-h-screen app-page-bg flex items-center justify-center p-4">
        <div className="rounded-2xl border border-border/70 bg-card/80 shadow-card px-6 py-10 text-center max-w-md">
          <p className="text-muted-foreground mb-4">Bitte melde dich an, um Projekte zu sehen.</p>
          <Button asChild>
            <Link href="/login?from=/projects">Zum Login</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <AppLayout>
      <PageContainer>
        <PageHeader
          title="Projekte"
          description={
            user
              ? `${projects.length} Projekt${projects.length === 1 ? "" : "e"} · ${
                  user.is_admin ? "Administrator" : "Benutzer"
                }`
              : undefined
          }
        />

        <div className="mb-8">
          <Button asChild>
            <Link href="/projects/new">
              <Plus className="w-4 h-4" />
              Neues Projekt anlegen
            </Link>
          </Button>
        </div>

        {error && user && (
          <p className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2 mb-6">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-center text-muted-foreground py-12">Lade Projekte…</p>
        ) : projects.length === 0 ? (
          <div className="rounded-2xl border border-border/70 bg-card/80 shadow-card px-6 py-14 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <FolderKanban className="w-7 h-7" />
            </div>
            <h3 className="font-display text-lg font-semibold mb-2">Noch keine Projekte</h3>
            <p className="text-muted-foreground max-w-md mx-auto mb-6">
              Lege dein erstes Projekt an und starte mit den Planungsschritten.
            </p>
            <Button asChild>
              <Link href="/projects/new">Projekt anlegen</Link>
            </Button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
      </PageContainer>
    </AppLayout>
  );
}

function ProjectCard({ project }: { project: Project }) {
  const typeLabel =
    project.project_type in WIZARD_PROJECT_TYPE_LABELS
      ? WIZARD_PROJECT_TYPE_LABELS[project.project_type as WizardProjectType]
      : project.project_type;

  return (
    <div className="relative group h-full">
      <div
        className={cn(
          "h-full min-h-[200px] flex flex-col rounded-2xl border border-border/70 bg-card/80",
          "shadow-card transition-all duration-200 stat-card",
          "hover:border-primary/30 hover:shadow-card-hover hover:-translate-y-0.5"
        )}
      >
        <Link
          href={`/projects/${project.key}/planung`}
          className="flex flex-col flex-1 cursor-pointer p-5 sm:p-6"
        >
          <div className="flex items-start gap-3 mb-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
              <FolderKanban className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-mono text-muted-foreground mb-0.5">{project.key}</p>
              <h2 className="font-display text-lg font-semibold tracking-tight truncate group-hover:text-primary transition-colors">
                {project.name}
              </h2>
              {typeLabel && (
                <p className="text-xs text-muted-foreground mt-1">{typeLabel}</p>
              )}
              {project.description ? (
                <p className="text-sm text-muted-foreground line-clamp-2 mt-1">{project.description}</p>
              ) : null}
            </div>
          </div>
          <div className="flex items-center text-xs text-muted-foreground mt-auto">
            <Clock className="w-3 h-3 mr-1" />
            {new Date(project.updated_at).toLocaleDateString("de-CH")}
          </div>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary opacity-0 group-hover:opacity-100 transition-opacity">
            Planung öffnen <ChevronRight className="w-4 h-4" />
          </span>
        </Link>
      </div>
    </div>
  );
}
