import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";

export function BackLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors mb-4",
        className
      )}
    >
      <ArrowLeft className="w-4 h-4" />
      {children}
    </Link>
  );
}
