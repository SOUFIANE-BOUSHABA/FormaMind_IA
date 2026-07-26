import {
  BookOpenCheck,
  CheckCircle2,
  Clock3,
  FileText,
  Loader2,
  Play,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { useParams } from "react-router-dom";

import { cn } from "@/lib/utils";
import {
  useLearningPlan,
  useUpdateLearningActivityStatus,
} from "@/features/learning-plan/hooks/useLearningPlans";
import {
  type LearningActivity,
  type LearningActivityStatus,
  type LearningPlan,
} from "@/features/learning-plan/types/learning-plan";

const statusLabels: Record<LearningActivityStatus, string> = {
  completed: "Terminee",
  in_progress: "En cours",
  pending: "A faire",
};

function nextStatus(status: LearningActivityStatus): LearningActivityStatus {
  if (status === "pending") {
    return "in_progress";
  }
  if (status === "in_progress") {
    return "completed";
  }
  return "in_progress";
}

function statusIcon(status: LearningActivityStatus) {
  if (status === "completed") {
    return CheckCircle2;
  }
  if (status === "in_progress") {
    return Play;
  }
  return BookOpenCheck;
}

function PlanHeader({ plan }: { plan: LearningPlan }) {
  return (
    <section className="rounded-[32px] border border-primary/10 bg-white p-7 shadow-card lg:p-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Genere par Learning Coach Agent
          </p>
          <h1 className="mt-2 font-heading text-4xl font-extrabold">
            {plan.title}
          </h1>
          <p className="mt-3 max-w-3xl leading-7 text-foreground/60">
            {plan.generatedSummary}
          </p>
        </div>
        <div className="rounded-3xl bg-primary p-6 text-white shadow-elevated">
          <p className="text-xs font-extrabold uppercase text-white/70">
            Progression globale
          </p>
          <p className="mt-2 font-heading text-5xl font-black">
            {plan.progressPercentage}%
          </p>
        </div>
      </div>

      <div className="mt-7 h-3 overflow-hidden rounded-full bg-primary/10">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${plan.progressPercentage}%` }}
        />
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        <div className="rounded-2xl bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Evaluation
          </p>
          <p className="mt-1 font-bold">{plan.assessmentTitle}</p>
        </div>
        <div className="rounded-2xl bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Minutes
          </p>
          <p className="mt-1 font-bold">{plan.dailyMinutes} min/jour</p>
        </div>
        <div className="rounded-2xl bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Debut
          </p>
          <p className="mt-1 font-bold">{plan.startDate}</p>
        </div>
        <div className="rounded-2xl bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Fin cible
          </p>
          <p className="mt-1 font-bold">{plan.targetEndDate}</p>
        </div>
      </div>
    </section>
  );
}

function ActivityCard({
  activity,
  planId,
}: {
  activity: LearningActivity;
  planId: number;
}) {
  const updateMutation = useUpdateLearningActivityStatus(planId);
  const Icon = statusIcon(activity.status);
  const targetStatus = nextStatus(activity.status);

  return (
    <article className="rounded-2xl border border-border bg-white p-5 shadow-card">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex gap-4">
          <span
            className={cn(
              "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl",
              activity.status === "completed"
                ? "bg-success/10 text-success"
                : activity.status === "in_progress"
                  ? "bg-primary text-white"
                  : "bg-primary/10 text-primary",
            )}
          >
            <Icon className="h-6 w-6" />
          </span>
          <div>
            <p className="font-ui text-xs font-extrabold uppercase text-primary">
              {activity.type} · {statusLabels[activity.status]}
            </p>
            <h3 className="mt-1 font-heading text-2xl font-extrabold">
              {activity.title}
            </h3>
            <p className="mt-2 leading-7 text-foreground/65">
              {activity.instructions}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 rounded-full bg-surface-muted px-4 py-2 text-sm font-bold text-foreground/60">
          <Clock3 className="h-4 w-4 text-primary" />
          {activity.durationMinutes} min
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {activity.sources.map((source) => (
          <div
            className="rounded-2xl border border-primary/10 bg-primary/5 p-4"
            key={`${activity.id}-${source.documentId}-${source.pageNumber}`}
          >
            <p className="flex items-center gap-2 font-bold text-primary">
              <FileText className="h-4 w-4" />
              {source.documentTitle}, page {source.pageNumber}
            </p>
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-foreground/55">
              {source.excerpt}
            </p>
          </div>
        ))}
      </div>

      <button
        className="mt-5 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 font-bold text-white transition hover:bg-secondary disabled:opacity-60"
        disabled={updateMutation.isPending}
        onClick={() => {
          updateMutation.mutate({
            activityId: activity.id,
            status: targetStatus,
          });
        }}
        type="button"
      >
        {activity.status === "completed" ? (
          <RotateCcw className="h-4 w-4" />
        ) : (
          <CheckCircle2 className="h-4 w-4" />
        )}
        {activity.status === "pending"
          ? "Commencer"
          : activity.status === "in_progress"
            ? "Marquer terminee"
            : "Reouvrir"}
      </button>
    </article>
  );
}

export function LearningPlanDetailPage() {
  const params = useParams();
  const planId = Number(params.planId);
  const planQuery = useLearningPlan(Number.isFinite(planId) ? planId : null);

  if (planQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (planQuery.isError || !planQuery.data) {
    return (
      <div className="px-4 py-8 pb-28 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger le plan.
        </div>
      </div>
    );
  }

  const plan = planQuery.data;

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1180px] space-y-6">
        <PlanHeader plan={plan} />

        <div className="rounded-[32px] border border-primary/10 bg-gradient-to-br from-primary/5 to-secondary/5 p-6 shadow-card">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-white">
              <Sparkles className="h-6 w-6" />
            </span>
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Planning hebdo
              </p>
              <h2 className="font-heading text-2xl font-extrabold">
                Modules et activites
              </h2>
            </div>
          </div>

          <div className="mt-6 space-y-6">
            {plan.modules.map((module) => (
              <section
                className="rounded-[28px] border border-primary/10 bg-white/70 p-5"
                key={module.id}
              >
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <p className="font-ui text-xs font-extrabold uppercase text-primary">
                      Module {module.orderIndex + 1} · {module.priority}
                    </p>
                    <h2 className="mt-1 font-heading text-3xl font-extrabold">
                      {module.title}
                    </h2>
                    <p className="mt-2 max-w-3xl leading-7 text-foreground/60">
                      {module.objective}
                    </p>
                  </div>
                  <span className="w-fit rounded-full bg-surface-muted px-4 py-2 text-sm font-bold">
                    {module.estimatedMinutes} min
                  </span>
                </div>

                <div className="mt-5 space-y-4">
                  {module.activities.map((activity) => (
                    <ActivityCard
                      activity={activity}
                      key={activity.id}
                      planId={plan.id}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
