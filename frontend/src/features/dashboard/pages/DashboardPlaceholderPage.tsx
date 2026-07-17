import { LogOut } from "lucide-react";

import { useAuth } from "@/features/auth/hooks/useAuth";

export function DashboardPlaceholderPage() {
  const auth = useAuth();

  return (
    <main className="min-h-screen bg-background px-6 py-12 text-foreground">
      <section className="mx-auto flex max-w-4xl flex-col gap-8">
        <div className="flex flex-col justify-between gap-5 border-b border-border pb-6 sm:flex-row sm:items-center">
          <div>
            <p className="font-ui text-sm font-semibold uppercase text-primary">
              FormaMind AI
            </p>
            <h1 className="mt-2 font-heading text-4xl font-extrabold">
              Tableau de bord
            </h1>
          </div>
          <button
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-white px-4 py-2.5 font-ui text-sm font-semibold text-foreground shadow-card transition hover:border-primary hover:text-primary"
            onClick={auth.logout}
            type="button"
          >
            <LogOut className="h-4 w-4" />
            Déconnexion
          </button>
        </div>

        <div className="rounded-lg border border-border bg-white p-8 shadow-card">
          <p className="text-lg text-foreground/70">
            Bonjour {auth.user?.fullName ?? "Rabie"}, votre authentification est
            active.
          </p>
          <p className="mt-3 text-sm text-foreground/55">
            Les fonctionnalités du tableau de bord seront ajoutées dans les
            prochaines étapes.
          </p>
        </div>
      </section>
    </main>
  );
}
