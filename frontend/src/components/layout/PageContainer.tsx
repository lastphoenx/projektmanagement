import { cn } from "@/lib/utils";
import { LAYOUT_MAX_WIDTH_CLASS, LAYOUT_SHELL_CLASS } from "@/lib/layout-shell";

export type PageContainerWidth = "default" | "medium" | "narrow" | "wide";

const WIDTH_CLASSES: Record<PageContainerWidth, string> = {
  default: LAYOUT_MAX_WIDTH_CLASS,
  medium: "max-w-4xl",
  narrow: "max-w-3xl",
  wide: "max-w-7xl",
};

export function LayoutShell({
  children,
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div className={cn(LAYOUT_SHELL_CLASS, className)} {...props}>
      {children}
    </div>
  );
}

export function PageContainer({
  children,
  className,
  width = "default",
  ...props
}: React.ComponentProps<"div"> & { width?: PageContainerWidth }) {
  return (
    <div
      className={cn("mx-auto w-full px-4 sm:px-6 py-6 sm:py-8", WIDTH_CLASSES[width], className)}
      {...props}
    >
      {children}
    </div>
  );
}
