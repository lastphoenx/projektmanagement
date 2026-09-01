"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

/** Projekt-Hub: Weiterleitung zur Planung (Phase 4 Kern). */
export default function ProjectHubPage() {
  const params = useParams();
  const router = useRouter();
  const projectKey = params.key as string;

  useEffect(() => {
    if (projectKey) {
      router.replace(`/projects/${projectKey}/planung`);
    }
  }, [projectKey, router]);

  return (
    <div className="min-h-screen app-page-bg flex items-center justify-center">
      <p className="text-muted-foreground">Weiterleitung zur Planung…</p>
    </div>
  );
}
