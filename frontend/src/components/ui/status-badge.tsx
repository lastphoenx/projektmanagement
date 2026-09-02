import { cn } from "@/lib/utils";

const styles: Record<string, string> = {
  pending: "bg-muted text-muted-foreground border-border/80",
  draft: "bg-amber-50 text-amber-800 border-amber-200",
  approved: "bg-emerald-50 text-emerald-800 border-emerald-200",
};

export function StatusBadge({
  status,
  label,
  className,
}: {
  status: string;
  label: string;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        styles[status] ?? styles.pending,
        className
      )}
    >
      {label}
    </span>
  );
}
