"use client";

import { Eye, Pencil, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InlineAlert } from "@/components/ui/inline-alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { STATUS_LABELS } from "@/lib/planning-steps";
import { cn } from "@/lib/utils";

type ContentMode = "read" | "edit";

export function PlanningDocumentPanel({
  title,
  description,
  status,
  content,
  draftContent,
  onDraftChange,
  contentMode,
  onContentModeChange,
  showPreview,
  onShowPreviewChange,
  placeholder,
  children,
}: {
  title: string;
  description: string;
  status?: string;
  content: string;
  draftContent: string;
  onDraftChange: (value: string) => void;
  contentMode: ContentMode;
  onContentModeChange: (mode: ContentMode) => void;
  showPreview: boolean;
  onShowPreviewChange: (show: boolean) => void;
  placeholder: string;
  children?: React.ReactNode;
}) {
  const hasContent = content.trim().length > 0;
  const statusKey = status ?? "pending";
  const statusLabel = STATUS_LABELS[statusKey] ?? statusKey;

  function enterEdit() {
    onContentModeChange("edit");
  }

  function exitEdit() {
    onContentModeChange("read");
    onShowPreviewChange(false);
  }

  return (
    <section className="rounded-2xl border border-border/70 bg-card/80 shadow-card p-5 sm:p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h2 className="font-display text-xl font-semibold">{title}</h2>
            {status && statusKey !== "pending" && (
              <StatusBadge status={statusKey} label={statusLabel} />
            )}
          </div>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {contentMode === "read" ? (
            <Button type="button" variant="outline" size="sm" onClick={enterEdit}>
              <Pencil className="w-4 h-4" />
              {hasContent ? "Bearbeiten" : "Inhalt erfassen"}
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant={showPreview ? "secondary" : "outline"}
                size="sm"
                onClick={() => onShowPreviewChange(!showPreview)}
              >
                <Eye className="w-4 h-4" />
                Vorschau
              </Button>
              <Button type="button" variant="default" size="sm" onClick={exitEdit}>
                <X className="w-4 h-4" />
                Fertig
              </Button>
            </>
          )}
        </div>
      </div>

      {contentMode === "edit" && (
        <InlineAlert variant="edit" className="mb-4">
          Du bearbeitest diesen Schritt — Inhalt speichern, dann «Fertig».
        </InlineAlert>
      )}

      {children}

      {contentMode === "read" ? (
        <div className="planning-read-panel">
          {hasContent ? (
            <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-foreground">
              {content}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">
              Noch kein Inhalt. «Inhalt erfassen» oder KI/Generator nutzen.
            </p>
          )}
        </div>
      ) : (
        <div
          className={cn(
            showPreview ? "grid lg:grid-cols-2 gap-4" : "space-y-2"
          )}
        >
          <div className="space-y-2">
            {!showPreview && (
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Bearbeiten
              </label>
            )}
            <textarea
              value={draftContent}
              onChange={(e) => onDraftChange(e.target.value)}
              rows={showPreview ? 20 : 22}
              className="planning-editor-field w-full"
              placeholder={placeholder}
            />
          </div>
          {showPreview && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Live-Vorschau
              </label>
              <div className="planning-preview-panel">
                {draftContent.trim() ? (
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {draftContent}
                  </pre>
                ) : (
                  <span className="text-muted-foreground text-sm">Noch kein Inhalt.</span>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
