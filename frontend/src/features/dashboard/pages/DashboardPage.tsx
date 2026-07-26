import {
  ArrowRight,
  Award,
  BookOpen,
  CheckSquare,
  Clock3,
  FileText,
  Sparkles,
  Stars,
  Target,
  Timer,
  TrendingUp,
  Verified,
  Wand2,
} from "lucide-react";
import { Link } from "react-router-dom";

import { cn } from "@/lib/utils";
import { useDashboardSummary } from "@/features/dashboard/hooks/useDashboardSummary";
import {
  type AgentActivity,
  type DashboardMetric,
  type DashboardTone,
  type SkillMetric,
} from "@/features/dashboard/types/dashboard";

const metricIcons = {
  award: Award,
  book: BookOpen,
  checklist: CheckSquare,
  target: Target,
  timer: Clock3,
  verified: Verified,
} as const;

const toneClasses: Record<
  DashboardTone,
  {
    bg: string;
    border: string;
    fill: string;
    soft: string;
    text: string;
  }
> = {
  accent: {
    bg: "bg-accent",
    border: "border-accent/20",
    fill: "bg-accent",
    soft: "bg-accent/10",
    text: "text-accent",
  },
  error: {
    bg: "bg-error",
    border: "border-error/20",
    fill: "bg-error",
    soft: "bg-error/10",
    text: "text-error",
  },
  primary: {
    bg: "bg-primary",
    border: "border-primary/20",
    fill: "bg-primary",
    soft: "bg-primary/10",
    text: "text-primary",
  },
  secondary: {
    bg: "bg-secondary",
    border: "border-secondary/20",
    fill: "bg-secondary",
    soft: "bg-secondary/10",
    text: "text-secondary",
  },
  success: {
    bg: "bg-success",
    border: "border-success/20",
    fill: "bg-success",
    soft: "bg-success/10",
    text: "text-success",
  },
  warning: {
    bg: "bg-warning",
    border: "border-warning/20",
    fill: "bg-warning",
    soft: "bg-warning/10",
    text: "text-warning",
  },
};

function DashboardSkeleton() {
  return (
    <div className="space-y-8 px-4 py-8 pb-28 lg:px-10 lg:py-10">
      <div className="flex animate-pulse flex-col gap-4 lg:flex-row lg:justify-between">
        <div className="space-y-3">
          <div className="h-10 w-72 rounded-xl bg-primary/10" />
          <div className="h-5 w-96 max-w-full rounded-lg bg-primary/10" />
        </div>
        <div className="h-14 w-80 max-w-full rounded-xl bg-primary/10" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, index) => (
          <div
            className="h-44 animate-pulse rounded-2xl border border-border bg-white"
            key={index}
          />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="h-[480px] animate-pulse rounded-[32px] bg-white xl:col-span-8" />
        <div className="h-[480px] animate-pulse rounded-[32px] bg-foreground/10 xl:col-span-4" />
      </div>
    </div>
  );
}

function DashboardErrorState() {
  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-10">
      <div className="rounded-[28px] border border-error/20 bg-white p-8 text-error shadow-card">
        <p className="font-heading text-2xl font-bold">
          Impossible de charger le tableau de bord.
        </p>
        <p className="mt-2 text-sm text-foreground/60">
          Vérifiez que l’API est démarrée, puis actualisez la page.
        </p>
      </div>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center rounded-2xl border border-dashed border-border bg-surface-muted/60 p-6 text-center text-sm text-foreground/55">
      {label}
    </div>
  );
}

function MetricCard({ metric }: { metric: DashboardMetric }) {
  const Icon = metricIcons[metric.icon as keyof typeof metricIcons] ?? Sparkles;
  const tone = toneClasses[metric.tone];

  return (
    <article
      className={cn(
        "relative overflow-hidden rounded-2xl border bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-elevated",
        "bg-[radial-gradient(circle_at_2px_2px,rgba(79,70,229,0.06)_1px,transparent_0)] [background-size:16px_16px]",
        metric.progress !== null ? "border-primary/20 bg-primary/5" : tone.border,
      )}
    >
      <div className="mb-5 flex items-center justify-between gap-3">
        <span
          className={cn(
            "font-ui text-[10px] font-extrabold uppercase tracking-[0.18em]",
            metric.progress !== null ? "text-primary" : "text-foreground/55",
          )}
        >
          {metric.label}
        </span>
        <span
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg",
            metric.progress !== null ? "bg-primary text-white" : tone.soft,
            metric.progress !== null ? "" : tone.text,
          )}
        >
          <Icon className="h-5 w-5" />
        </span>
      </div>

      <div className="flex items-baseline gap-1">
        <span
          className={cn(
            "font-heading text-4xl font-black leading-none",
            metric.tone === "primary" || metric.progress !== null
              ? "text-primary"
              : "text-foreground",
          )}
        >
          {metric.value}
        </span>
        {metric.description.startsWith("/") ? (
          <span className="font-ui text-sm font-bold text-foreground/45">
            {metric.description}
          </span>
        ) : null}
      </div>

      {!metric.description.startsWith("/") ? (
        <p className="mt-3 text-xs font-medium leading-relaxed text-foreground/50">
          {metric.description}
        </p>
      ) : null}

      {metric.trend ? (
        <p className="mt-3 flex items-center gap-1 text-xs font-bold text-success">
          <TrendingUp className="h-4 w-4" />
          {metric.trend}
        </p>
      ) : null}

      {metric.progress !== null ? (
        <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-primary/10">
          <div
            className="h-full rounded-full bg-primary"
            style={{ width: `${metric.progress}%` }}
          />
        </div>
      ) : null}
    </article>
  );
}

function SkillsProfile({ skills }: { skills: SkillMetric[] }) {
  return (
    <section className="flex min-h-[480px] flex-col rounded-[32px] border border-primary/10 bg-white p-6 shadow-card lg:p-8">
      <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="font-heading text-2xl font-bold">
            Profil de Compétences IA
          </h2>
          <p className="mt-1 text-sm text-foreground/60">
            Visualisation de votre expertise multidimensionnelle
          </p>
        </div>
        <div className="flex w-fit rounded-xl bg-surface-muted p-1">
          <button
            className="rounded-lg px-5 py-2 text-sm font-semibold text-foreground/65"
            type="button"
          >
            Radar
          </button>
          <button
            className="rounded-lg bg-white px-5 py-2 text-sm font-bold text-primary shadow-card"
            type="button"
          >
            Analytique
          </button>
        </div>
      </div>

      {skills.length === 0 ? (
        <EmptyState label="Aucune compétence disponible pour le moment." />
      ) : (
        <div className="flex flex-1 items-end justify-between gap-4 overflow-x-auto px-2 pb-2">
          {skills.map((skill) => (
            <div
              className="group flex min-w-14 flex-col items-center gap-5"
              key={skill.label}
            >
              <div className="relative flex h-72 w-12 flex-col justify-end rounded-xl bg-surface-muted">
                <div
                  className={cn(
                    "w-full rounded-xl bg-gradient-to-b from-primary to-secondary shadow-[0_8px_18px_rgba(53,37,205,0.24)] transition-all duration-500 group-hover:brightness-110",
                    skill.highlighted ? "opacity-100" : "opacity-70",
                  )}
                  style={{ height: `${skill.value}%` }}
                />
                <span className="absolute -top-12 left-1/2 -translate-x-1/2 rounded-lg bg-foreground px-3 py-1.5 text-xs font-bold text-white opacity-0 shadow-card transition group-hover:opacity-100">
                  {skill.value}%
                </span>
              </div>
              <span
                className={cn(
                  "font-ui text-[11px] font-extrabold uppercase tracking-tight",
                  skill.highlighted ? "text-primary" : "text-foreground/65",
                )}
              >
                {skill.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function AgentsPanel({ agents }: { agents: AgentActivity[] }) {
  const statusLabel = {
    active: "Actif",
    online: "En ligne",
    waiting: "En attente",
  };

  return (
    <section className="relative overflow-hidden rounded-[32px] bg-[#283044] p-7 text-white shadow-elevated lg:p-8">
      <div className="pointer-events-none absolute right-0 top-0 h-48 w-48 bg-primary/20 blur-3xl" />
      <h2 className="relative z-10 mb-8 flex items-center gap-3 font-heading text-xl font-bold">
        <Sparkles className="h-6 w-6 text-[rgb(var(--color-accent-soft))]" />
        Agents IA en activité
      </h2>

      {agents.length === 0 ? (
        <div className="relative z-10 rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-white/60">
          Aucun agent actif pour le moment.
        </div>
      ) : (
        <div className="relative z-10 space-y-6">
          <div className="absolute bottom-8 left-[18px] top-10 w-px bg-gradient-to-b from-primary/50 via-accent/40 to-transparent" />
          {agents.map((agent) => {
            const tone = toneClasses[agent.tone];
            const isWaiting = agent.status === "waiting";

            return (
              <article className="relative flex gap-5" key={agent.name}>
                <span
                  className={cn(
                    "relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border",
                    isWaiting
                      ? "border-white/10 bg-white/5 text-white/40"
                      : `${tone.border} ${tone.soft} ${tone.text}`,
                  )}
                >
                  {agent.status === "active" ? (
                    <BotIcon />
                  ) : (
                    <FileText className="h-5 w-5" />
                  )}
                </span>
                <div
                  className={cn(
                    "flex-1 rounded-2xl border p-4 transition",
                    isWaiting
                      ? "border-white/5 bg-white/5 opacity-55"
                      : agent.status === "active"
                        ? "border-primary/40 bg-white/10 shadow-[0_10px_30px_rgba(53,37,205,0.14)]"
                        : "border-white/10 bg-white/5",
                  )}
                >
                  <div className="mb-1 flex items-start justify-between gap-3">
                    <p className="text-sm font-bold">{agent.name}</p>
                    <span
                      className={cn(
                        "flex items-center gap-1.5 font-ui text-[9px] font-black uppercase tracking-widest",
                        isWaiting ? "text-white/35" : tone.text,
                      )}
                    >
                      <span
                        className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          isWaiting ? "bg-white/30" : tone.fill,
                        )}
                      />
                      {statusLabel[agent.status]}
                    </span>
                  </div>
                  <p
                    className={cn(
                      "text-xs leading-relaxed",
                      isWaiting ? "text-white/40" : "text-white/65",
                    )}
                  >
                    {agent.description}
                  </p>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <button
        className="relative z-10 mt-8 w-full rounded-xl border border-white/15 py-3 text-sm font-bold text-white/85 transition hover:bg-white/5"
        type="button"
      >
        Centre de contrôle Multi-Agents
      </button>
    </section>
  );
}

function BotIcon() {
  return <Sparkles className="h-5 w-5" />;
}

export function DashboardPage() {
  const summaryQuery = useDashboardSummary();

  if (summaryQuery.isPending) {
    return <DashboardSkeleton />;
  }

  if (summaryQuery.isError) {
    return <DashboardErrorState />;
  }

  const summary = summaryQuery.data;

  return (
    <div className="space-y-8 px-4 py-8 pb-28 lg:px-10 lg:py-10">
      <section className="flex flex-col justify-between gap-6 xl:flex-row xl:items-start">
        <div>
          <h1 className="font-heading text-4xl font-extrabold tracking-tight md:text-5xl">
            {summary.greeting.replace(summary.learnerName, "")}
            <span className="text-primary">{summary.learnerName}</span>,
          </h1>
          <p className="mt-3 max-w-2xl text-lg leading-8 text-foreground/65">
            {summary.subtitle}
          </p>
        </div>
       
      </section>

      {summary.metrics.length === 0 ? (
        <EmptyState label="Aucun indicateur disponible pour le moment." />
      ) : (
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {summary.metrics.map((metric) => (
            <MetricCard key={metric.label} metric={metric} />
          ))}
        </section>
      )}

      <section className="grid grid-cols-1 gap-6 xl:grid-cols-12">
        <div className="space-y-6 xl:col-span-8">
          <SkillsProfile skills={summary.skills} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="rounded-[32px] border border-primary/10 bg-gradient-to-br from-primary/5 to-secondary/5 p-7 shadow-card lg:p-8">
              <div className="mb-7 flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <Stars className="h-6 w-6" />
                </span>
                <h2 className="font-heading text-xl font-bold">
                  Recommandation
                </h2>
              </div>

              {summary.recommendation === null ? (
                <EmptyState label="Aucune recommandation disponible." />
              ) : (
                <div className="space-y-4">
                  <div>
                    <p className="font-ui text-[10px] font-black uppercase tracking-[0.2em] text-primary">
                      {summary.recommendation.eyebrow}
                    </p>
                    <h3 className="mt-1 font-heading text-2xl font-bold">
                      {summary.recommendation.title}
                    </h3>
                  </div>
                  <div className="flex flex-wrap gap-5 text-sm text-foreground/60">
                    <span className="flex items-center gap-2">
                      <Timer className="h-4 w-4" />
                      {summary.recommendation.duration}
                    </span>
                    <span className="flex items-center gap-2">
                      <Verified className="h-4 w-4" />
                      {summary.recommendation.badge}
                    </span>
                  </div>
                  <p className="text-sm leading-7 text-foreground/65">
                    {summary.recommendation.description}
                  </p>
                  {summary.recommendation.planId ? (
                    <Link
                      className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-4 font-bold text-white shadow-[0_12px_24px_rgba(53,37,205,0.2)] transition hover:bg-secondary"
                      to={`/learning-plans/${summary.recommendation.planId}`}
                    >
                      {summary.recommendation.actionLabel}
                      <ArrowRight className="h-5 w-5" />
                    </Link>
                  ) : (
                    <Link
                      className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-4 font-bold text-white shadow-[0_12px_24px_rgba(53,37,205,0.2)] transition hover:bg-secondary"
                      to="/assessments"
                    >
                      {summary.recommendation.actionLabel}
                      <ArrowRight className="h-5 w-5" />
                    </Link>
                  )}
                </div>
              )}
            </section>

            <section className="rounded-[32px] border border-primary/10 bg-white p-7 shadow-card lg:p-8">
              <div className="mb-7 flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-full bg-error/10 text-error">
                  <Wand2 className="h-6 w-6" />
                </span>
                <h2 className="font-heading text-xl font-bold">
                  Points de focus
                </h2>
              </div>

              {summary.focusAreas.length === 0 ? (
                <EmptyState label="Aucun point de focus prioritaire." />
              ) : (
                <div className="space-y-6">
                  {summary.focusAreas.map((focus) => {
                    const isCritical = focus.severity === "critical";
                    return (
                      <div key={focus.label}>
                        <div className="mb-2 flex items-center justify-between gap-3">
                          <p className="text-sm font-bold">{focus.label}</p>
                          <span
                            className={cn(
                              "rounded border px-2 py-0.5 font-ui text-[10px] font-black uppercase",
                              isCritical
                                ? "border-error/10 bg-error/5 text-error"
                                : "border-secondary/10 bg-secondary/5 text-secondary",
                            )}
                          >
                            {isCritical ? "Critique" : "Important"}
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-surface-muted">
                          <div
                            className={cn(
                              "h-full rounded-full",
                              isCritical ? "bg-error" : "bg-secondary",
                            )}
                            style={{ width: `${focus.progress}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                  <button
                    className="w-full rounded-xl bg-surface-muted py-3 text-sm font-bold text-primary transition hover:bg-primary/5"
                    type="button"
                  >
                    Générer un plan de remédiation
                  </button>
                </div>
              )}
            </section>
          </div>
        </div>

        <div className="space-y-6 xl:col-span-4">
          <AgentsPanel agents={summary.agents} />

          <section className="rounded-[32px] border border-primary/10 bg-white p-7 shadow-card lg:p-8">
            <h2 className="mb-7 font-heading text-xl font-bold">
              Journal d'activité
            </h2>
            {summary.recentActivity.length === 0 ? (
              <EmptyState label="Aucune activité récente." />
            ) : (
              <div className="max-h-80 space-y-7 overflow-y-auto pr-2">
                {summary.recentActivity.map((activity, index) => {
                  const tone = toneClasses[activity.tone];
                  return (
                    <div className="flex gap-4" key={activity.title}>
                      <div className="flex flex-col items-center">
                        <span className={cn("h-2 w-2 rounded-full", tone.fill)} />
                        {index < summary.recentActivity.length - 1 ? (
                          <span className="my-1 h-full min-h-10 w-px bg-surface-muted" />
                        ) : null}
                      </div>
                      <div className="flex-1 pb-1">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-sm font-bold">{activity.title}</p>
                          <span className="whitespace-nowrap text-xs text-foreground/45">
                            {activity.timestamp}
                          </span>
                        </div>
                        <p className="mt-1 text-xs leading-relaxed text-foreground/60">
                          {activity.description}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </section>
    </div>
  );
}
