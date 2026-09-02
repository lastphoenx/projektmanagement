"use client";

import { Loader2, Pencil, Save, X } from "lucide-react";
import { BackLink } from "@/components/layout/BackLink";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Project } from "@/lib/api";

export function PlanningPageHeader({
  projectKey,
  project,
  typeLabel,
  editingName,
  nameDraft,
  nameSaving,
  onNameDraftChange,
  onStartNameEdit,
  onCancelNameEdit,
  onSaveNameEdit,
}: {
  projectKey: string;
  project: Project | null;
  typeLabel: string | null | undefined;
  editingName: boolean;
  nameDraft: string;
  nameSaving: boolean;
  onNameDraftChange: (value: string) => void;
  onStartNameEdit: () => void;
  onCancelNameEdit: () => void;
  onSaveNameEdit: () => void;
}) {
  return (
    <div className="mb-6">
      <BackLink href="/projects">Projekte</BackLink>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-mono text-muted-foreground mb-1">{projectKey}</p>
          {editingName ? (
            <div className="flex flex-wrap items-center gap-2 max-w-xl">
              <Input
                value={nameDraft}
                onChange={(e) => onNameDraftChange(e.target.value)}
                className="font-display text-lg font-semibold h-10"
                maxLength={256}
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") void onSaveNameEdit();
                  if (e.key === "Escape") onCancelNameEdit();
                }}
              />
              <Button type="button" size="sm" onClick={() => void onSaveNameEdit()} disabled={nameSaving}>
                {nameSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                Speichern
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={onCancelNameEdit} disabled={nameSaving}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <h1 className="font-display text-2xl sm:text-3xl font-semibold tracking-tight">
                {project?.name ?? "Planung"}
              </h1>
              {project && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground"
                  onClick={onStartNameEdit}
                  title="Projektname bearbeiten"
                >
                  <Pencil className="w-4 h-4" />
                </Button>
              )}
            </div>
          )}
          {typeLabel && <p className="text-sm text-muted-foreground mt-1">{typeLabel}</p>}
        </div>
      </div>
    </div>
  );
}
