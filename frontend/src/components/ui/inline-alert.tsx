import { cn } from "@/lib/utils";

type InlineAlertVariant = "error" | "info" | "success" | "edit";

const variantClass: Record<InlineAlertVariant, string> = {
  error: "text-destructive bg-destructive/10 border-destructive/20",
  info: "text-foreground bg-muted/50 border-border/70",
  success: "text-emerald-800 bg-emerald-50 border-emerald-200",
  edit: "text-emerald-900 bg-emerald-50 border-emerald-200",
};

export function InlineAlert({
  variant = "error",
  className,
  children,
}: {
  variant?: InlineAlertVariant;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <p
      className={cn(
        "text-sm border rounded-lg px-3 py-2",
        variantClass[variant],
        className
      )}
      role={variant === "error" ? "alert" : undefined}
    >
      {children}
    </p>
  );
}
