import {
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  FileText,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Map,
  Menu,
  PanelLeftClose,
  Search,
  Settings,
  ShieldQuestion,
  Sparkles,
  UserCircle,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/hooks/useAuth";

type NavigationItem = {
  label: string;
  path: string;
  icon: typeof LayoutDashboard;
};

const navigationItems: NavigationItem[] = [
  { label: "Tableau de bord", path: "/dashboard", icon: LayoutDashboard },
  { label: "Documents", path: "/documents", icon: FileText },
  { label: "Assistant pédagogique", path: "/assistant", icon: Bot },
  { label: "Évaluations", path: "/assessments", icon: ShieldQuestion },
  { label: "Plan d'apprentissage", path: "/learning-plan", icon: Map },
  { label: "Simulation de soutenance", path: "/soutenance", icon: Sparkles },
  { label: "Rapports", path: "/reports", icon: BarChart3 },
  { label: "Paramètres", path: "/settings", icon: Settings },
];

function getInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function BrandMark() {
  return (
    <div className="flex items-center gap-3 px-6">
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white shadow-card">
        <Sparkles className="h-5 w-5 text-primary" />
      </div>
      <div>
        <p className="font-heading text-xl font-extrabold leading-none">
          FormaMind AI
        </p>
        <p className="mt-1 font-ui text-[10px] font-bold uppercase tracking-[0.22em] text-primary">
          Intelligence Pro
        </p>
      </div>
    </div>
  );
}

type SidebarContentProps = {
  onNavigate?: () => void;
};

function SidebarContent({ onNavigate }: SidebarContentProps) {
  const auth = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    auth.logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-full flex-col py-6">
      <BrandMark />

      <nav className="mt-10 flex-1 space-y-1 overflow-y-auto px-5">
        {navigationItems.map((item) => (
          <NavLink
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-r-lg border-l-4 px-4 py-3 font-ui text-[15px] transition",
                isActive
                  ? "border-primary bg-[rgb(var(--color-primary-soft))] font-bold text-foreground"
                  : "border-transparent text-foreground/65 hover:bg-white/50 hover:text-foreground",
              )
            }
            key={item.path}
            onClick={onNavigate}
            to={item.path}
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-5 px-5">
        <button
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3.5 font-ui font-bold text-primary-foreground shadow-elevated transition hover:bg-secondary"
          type="button"
        >
          <BookOpen className="h-5 w-5" />
          Nouvelle session
        </button>

        <div className="border-t border-border/70 pt-4">
          <a
            className="flex items-center gap-3 rounded-lg px-4 py-2 text-sm text-foreground/65 transition hover:bg-white/50 hover:text-foreground"
            href="#help"
          >
            <HelpCircle className="h-5 w-5" />
            Centre d'aide
          </a>
          <button
            className="flex w-full items-center gap-3 rounded-lg px-4 py-2 text-sm text-error transition hover:bg-error/5"
            onClick={handleLogout}
            type="button"
          >
            <LogOut className="h-5 w-5" />
            Déconnexion
          </button>
        </div>
      </div>
    </div>
  );
}

export function AppShell() {
  const auth = useAuth();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const navigate = useNavigate();

  const initials = useMemo(
    () => getInitials(auth.user?.fullName ?? "Rabie"),
    [auth.user?.fullName],
  );

  function handleLogout() {
    auth.logout();
    setIsUserMenuOpen(false);
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-[rgb(var(--color-surface-ai))] text-foreground">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-sidebar flex-col bg-surface-muted shadow-card md:flex">
        <SidebarContent />
      </aside>

      {isMobileOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            aria-label="Fermer la navigation"
            className="absolute inset-0 bg-foreground/30"
            onClick={() => {
              setIsMobileOpen(false);
            }}
            type="button"
          />
          <aside className="absolute inset-y-0 left-0 w-[82vw] max-w-sm bg-surface-muted shadow-elevated">
            <div className="absolute right-4 top-4">
              <button
                aria-label="Fermer le menu"
                className="rounded-full p-2 text-foreground/65 hover:bg-white"
                onClick={() => {
                  setIsMobileOpen(false);
                }}
                type="button"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <SidebarContent
              onNavigate={() => {
                setIsMobileOpen(false);
              }}
            />
          </aside>
        </div>
      ) : null}

      <div className="md:pl-sidebar">
        <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-border/50 bg-white/70 px-4 shadow-sm backdrop-blur-xl lg:px-8">
          <div className="flex min-w-0 flex-1 items-center gap-4">
            <button
              aria-label="Ouvrir la navigation"
              className="rounded-full p-2 text-foreground/70 hover:bg-surface-muted md:hidden"
              onClick={() => {
                setIsMobileOpen(true);
              }}
              type="button"
            >
              <Menu className="h-6 w-6" />
            </button>

            <div className="relative hidden w-full max-w-xl lg:block">
              <Search className="absolute left-5 top-1/2 h-5 w-5 -translate-y-1/2 text-foreground/45" />
              <input
                className="h-12 w-full rounded-full border-0 bg-surface-muted pl-14 pr-5 text-sm outline-none ring-1 ring-transparent transition placeholder:text-foreground/40 focus:ring-primary/20"
                placeholder="Rechercher une compétence..."
                type="search"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-5">
            <button
              aria-label="Notifications"
              className="relative rounded-full p-2.5 text-foreground/65 transition hover:bg-surface-muted hover:text-foreground"
              type="button"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-error ring-2 ring-white" />
            </button>
            <button
              aria-label="Paramètres"
              className="rounded-full p-2.5 text-foreground/65 transition hover:bg-surface-muted hover:text-foreground"
              type="button"
            >
              <Settings className="h-5 w-5" />
            </button>

            <div className="relative border-l border-border pl-3 sm:pl-5">
              <button
                aria-expanded={isUserMenuOpen}
                className="flex items-center gap-3"
                onClick={() => {
                  setIsUserMenuOpen((current) => !current);
                }}
                type="button"
              >
                <div className="hidden text-right sm:block">
                  <p className="font-ui text-sm font-semibold">
                    {auth.user?.fullName ?? "Rabie"}
                  </p>
                  <p className="font-ui text-[9px] font-extrabold uppercase tracking-widest text-primary">
                    Premium AI Plan
                  </p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-full border-2 border-primary/20 bg-white p-0.5 shadow-card">
                  <span className="flex h-full w-full items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
                    {initials || <UserCircle className="h-6 w-6" />}
                  </span>
                </span>
              </button>

              {isUserMenuOpen ? (
                <div className="absolute right-0 top-14 w-64 rounded-xl border border-border bg-white p-2 shadow-elevated">
                  <div className="border-b border-border px-3 py-3">
                    <p className="font-ui text-sm font-bold">
                      {auth.user?.fullName ?? "Rabie"}
                    </p>
                    <p className="truncate text-xs text-foreground/55">
                      {auth.user?.email}
                    </p>
                  </div>
                  <button
                    className="mt-2 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-error transition hover:bg-error/5"
                    onClick={handleLogout}
                    type="button"
                  >
                    <LogOut className="h-4 w-4" />
                    Déconnexion
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <main className="min-h-[calc(100vh-76px)]">
          <Outlet />
        </main>
      </div>

      <nav className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t border-border/70 bg-white/95 px-5 py-3 shadow-elevated backdrop-blur-xl md:hidden">
        {navigationItems.slice(0, 4).map((item) => (
          <NavLink
            aria-label={item.label}
            className={({ isActive }) =>
              cn(
                "rounded-full p-3 transition",
                isActive ? "bg-primary text-white" : "text-foreground/55",
              )
            }
            key={item.path}
            to={item.path}
          >
            <item.icon className="h-5 w-5" />
          </NavLink>
        ))}
        <button
          aria-label="Réduire la navigation"
          className="rounded-full p-3 text-foreground/55"
          onClick={() => {
            setIsMobileOpen(true);
          }}
          type="button"
        >
          <PanelLeftClose className="h-5 w-5" />
        </button>
      </nav>
    </div>
  );
}
