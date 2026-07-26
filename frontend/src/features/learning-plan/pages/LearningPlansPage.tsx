import {
  CalendarDays,
  Clock3,
  Loader2,
  Map,
  Plus,
  Sparkles,
  Trash2,
} from "lucide-react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import {
  useDeleteLearningPlan,
  useLearningPlans,
} from "@/features/learning-plan/hooks/useLearningPlans";
import {
  type LearningPlanIntensity,
  type LearningPlanListItem,
} from "@/features/learning-plan/types/learning-plan";

const intensityLabels: Record<LearningPlanIntensity, string> = {
  balanced: "Equilibre",
  intensive: "Intensif",
  light: "Leger",
};

function EmptyState() {
  return (
    <section className="flex min-h-[520px] flex-col items-center justify-center rounded-[32px] border border-dashed border-primary/20 bg-white p-8 text-center shadow-card">
      <span className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Map className="h-10 w-10" />
      </span>
      <h1 className="mt-6 font-heading text-3xl font-extrabold">
        Aucun plan d'apprentissage
      </h1>
      <p className="mt-3 max-w-xl leading-7 text-foreground/60">
        Terminez une evaluation, ouvrez ses resultats, puis demandez au Learning
        Coach Agent de creer un parcours personnalise.
      </p>
      <Link
        className="mt-7 inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-elevated transition hover:bg-secondary"
        to="/assessments"
      >
        <Plus className="h-5 w-5" />
        Aller aux evaluations
      </Link>
    </section>
  );
}

function PlanCard({ plan }: { plan: LearningPlanListItem }) {
  const deleteMutation = useDeleteLearningPlan();
  const isCompleted = plan.status === "completed";

  return (
    <article className="rounded-[28px] border border-primary/10 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-elevated">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase tracking-wide text-primary">
            Learning Coach Agent
          </p>
          <h2 className="mt-2 font-heading text-2xl font-extrabold">
            {plan.title}
          </h2>
          <p className="mt-2 text-sm text-foreground/55">
            Depuis {plan.assessmentTitle}
          </p>
        </div>
        <span
          className={cn(
            "w-fit rounded-full px-4 py-2 text-xs font-extrabold uppercase",
            isCompleted
              ? "bg-success/10 text-success"
              : "bg-primary/10 text-primary",
          )}
        >
          {isCompleted ? "Termine" : "Actif"}
        </span>
      </div>

      <div className="mt-6 h-2 overflow-hidden rounded-full bg-primary/10">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${plan.progressPercentage}%` }}
        />
      </div>

      <div className="mt-5 grid gap-3 text-sm text-foreground/60 sm:grid-cols-3">
        <span className="flex items-center gap-2 rounded-xl bg-surface-muted p-3">
          <Clock3 className="h-4 w-4 text-primary" />
          {plan.dailyMinutes} min/jour
        </span>
        <span className="flex items-center gap-2 rounded-xl bg-surface-muted p-3">
          <Sparkles className="h-4 w-4 text-primary" />
          {intensityLabels[plan.intensity]}
        </span>
        <span className="flex items-center gap-2 rounded-xl bg-surface-muted p-3">
          <CalendarDays className="h-4 w-4 text-primary" />
          Fin {plan.targetEndDate}
        </span>
      </div>

      {plan.nextActivityTitle ? (
        <div className="mt-5 rounded-2xl border border-primary/10 bg-primary/5 p-4">
          <p className="text-xs font-extrabold uppercase text-primary">
            Prochaine activite
          </p>
          <p className="mt-1 font-bold">{plan.nextActivityTitle}</p>
          <p className="mt-1 text-sm text-foreground/55">
            Planifiee le {plan.nextActivityDate}
          </p>
        </div>
      ) : null}

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Link
          className="flex flex-1 items-center justify-center rounded-xl bg-primary px-5 py-3 font-bold text-white transition hover:bg-secondary"
          to={`/learning-plans/${plan.id}`}
        >
          Ouvrir le plan
        </Link>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-error/20 px-5 py-3 font-bold text-error transition hover:bg-error/5"
          disabled={deleteMutation.isPending}
          onClick={() => {
            deleteMutation.mutate(plan.id);
          }}
          type="button"
        >
          <Trash2 className="h-4 w-4" />
          Supprimer
        </button>
      </div>
    </article>
  );
}

export function LearningPlansPage() {
  const plansQuery = useLearningPlans();

  if (plansQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (plansQuery.isError || !plansQuery.data) {
    return (
      <div className="px-4 py-8 pb-28 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger les plans d'apprentissage.
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1180px]">
        <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="font-ui text-xs font-extrabold uppercase text-primary">
              Planification
            </p>
            <h1 className="mt-2 font-heading text-4xl font-extrabold">
              Plan d'apprentissage personnalise
            </h1>
            <p className="mt-3 max-w-2xl leading-7 text-foreground/60">
              Suivez les parcours generes par le Learning Coach Agent a partir
              de vos evaluations et de vos sources.
            </p>
          </div>
          <Link
            className="inline-flex w-fit items-center gap-2 rounded-xl bg-primary px-5 py-3 font-bold text-white shadow-elevated transition hover:bg-secondary"
            to="/assessments"
          >
            <Plus className="h-5 w-5" />
            Nouveau depuis une evaluation
          </Link>
        </div>

        {plansQuery.data.items.length === 0 ? (
          <EmptyState />
        ) : (
          <section className="grid gap-5 xl:grid-cols-2">
            {plansQuery.data.items.map((plan) => (
              <PlanCard key={plan.id} plan={plan} />
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
