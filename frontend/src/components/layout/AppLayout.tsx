"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, FolderKanban, LayoutGrid, Shield, ShieldCheck, Sparkles } from "lucide-react";
import { LayoutShell } from "@/components/layout/PageContainer";
import { APP_COPYRIGHT, APP_NAME, APP_VERSION_LABEL } from "@/lib/appMeta";
import { fetchMe, logout, type User } from "@/lib/api";
import { cn } from "@/lib/utils";

const baseNavigation = [
  { name: "Projekte", href: "/projects", icon: FolderKanban },
  { name: "Portfolio", href: "/portfolio", icon: LayoutGrid },
  { name: "Status", href: "/", icon: Activity },
];

const adminNavigation = [
  { name: "KI-Einstellungen", href: "/admin/llm", icon: Sparkles },
  { name: "Sicherheit", href: "/admin/security", icon: Shield },
  { name: "Datenschutz", href: "/admin/privacy", icon: ShieldCheck },
];

interface AppLayoutProps {
  children: React.ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function handleLogout() {
    await logout();
    router.push("/login");
    router.refresh();
  }

  const roleLabel = user?.is_admin ? "Administrator" : "Benutzer";
  const navigation = user?.is_admin
    ? [...baseNavigation, ...adminNavigation]
    : baseNavigation;

  return (
    <div className="min-h-screen app-page-bg pb-14">
      <header className="app-chrome border-b border-white/10 sticky top-0 z-50 backdrop-blur-md bg-chrome/95">
        <LayoutShell className="py-2.5 flex items-center gap-3">
          <Link href="/projects" className="flex items-center gap-2.5 shrink-0 group">
            <div className="app-brand-logo">
              <span className="text-primary-foreground font-bold text-sm tracking-tight">PM</span>
            </div>
            <div className="flex items-center gap-2 leading-none">
              <span className="font-display font-semibold text-chrome-foreground text-sm tracking-tight">
                {APP_NAME}
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full border-0 bg-[#f59e0b] text-[#1f2937] font-extrabold uppercase tracking-wide">
                {APP_VERSION_LABEL}
              </span>
            </div>
          </Link>

          <nav className="hidden sm:flex items-center gap-0.5 flex-wrap justify-end shrink-0 ml-auto">
            {navigation.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname?.startsWith(item.href);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn("app-nav-link", isActive && "app-nav-link-active")}
                >
                  <item.icon className="w-4 h-4 mr-2" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </LayoutShell>
      </header>

      <main>{children}</main>

      <div className="fixed bottom-0 inset-x-0 z-50 border-t border-white/10 app-chrome backdrop-blur-md bg-chrome/95 text-xs sm:text-sm">
        <LayoutShell className="py-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
          <div className="flex flex-wrap items-center gap-x-1.5">
            {user ? (
              <>
                <span className="text-chrome-muted">Angemeldet:</span>
                <span className="font-medium text-chrome-foreground">{roleLabel}</span>
                <span className="text-chrome-muted">·</span>
                <span className="text-chrome-muted">
                  2FA {user.totp_enabled ? "aktiv" : "aus"}
                </span>
              </>
            ) : (
              <Link href="/login" className="text-chrome-muted hover:text-chrome-foreground">
                Anmelden
              </Link>
            )}
            {user && (
              <>
                <span className="text-chrome-muted/50 mx-1">·</span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="text-chrome-muted hover:text-chrome-foreground transition-colors"
                >
                  Abmelden
                </button>
              </>
            )}
          </div>
          <span className="text-chrome-muted/70 text-xs shrink-0">{APP_COPYRIGHT}</span>
        </LayoutShell>
      </div>
    </div>
  );
}
