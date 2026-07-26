import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";

import { useAttemptResults } from "@/features/assessments/hooks/useAssessments";
import { useGenerateLearningPlan } from "@/features/learning-plan/hooks/useLearningPlans";
import { type LearningPlanIntensity } from "@/features/learning-plan/types/learning-plan";

const formSchema = z.object({
  dailyMinutes: z.coerce.number().min(15).max(240),
  intensity: z.enum(["light", "balanced", "intensive"]),
  startDate: z.string().min(1),
  title: z.string().max(180).optional(),
});

type FormValues = z.infer<typeof formSchema>;

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export function GenerateLearningPlanPage() {
  const params = useParams();
  const navigate = useNavigate();
  const attemptId = Number(params.attemptId);
  const resultsQuery = useAttemptResults(Number.isFinite(attemptId) ? attemptId : null);
  const generateMutation = useGenerateLearningPlan();
  const form = useForm<FormValues>({
    defaultValues: {
      dailyMinutes: 45,
      intensity: "balanced",
      startDate: todayIso(),
      title: "",
    },
    resolver: zodResolver(formSchema),
  });

  function handleSubmit(values: FormValues) {
    generateMutation.mutate(
      {
        attemptId,
        dailyMinutes: values.dailyMinutes,
        intensity: values.intensity as LearningPlanIntensity,
        startDate: values.startDate,
        title: values.title?.trim() || null,
      },
      {
        onSuccess: (plan) => {
          navigate(`/learning-plans/${plan.id}`);
        },
      },
    );
  }

  if (resultsQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (resultsQuery.isError || !resultsQuery.data) {
    return (
      <div className="px-4 py-8 pb-28 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger la tentative evaluee.
        </div>
      </div>
    );
  }

  const results = resultsQuery.data;

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto grid max-w-[1180px] gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-[32px] border border-primary/10 bg-white p-7 shadow-card lg:p-8">
          <Link
            className="inline-flex items-center gap-2 text-sm font-bold text-primary"
            to={`/attempts/${attemptId}/results`}
          >
            <ArrowLeft className="h-4 w-4" />
            Retour aux resultats
          </Link>

          <p className="mt-8 font-ui text-xs font-extrabold uppercase text-primary">
            Learning Coach Agent
          </p>
          <h1 className="mt-2 font-heading text-4xl font-extrabold">
            Generer un plan personnalise
          </h1>
          <p className="mt-3 leading-7 text-foreground/60">
            Le coach va analyser votre tentative, retrouver les passages utiles
            dans les documents et organiser des taches concretes.
          </p>

          <div className="mt-7 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-primary/10 p-4 text-primary">
              <p className="text-xs font-extrabold uppercase">Score</p>
              <p className="mt-2 font-heading text-3xl font-black">
                {Math.round(results.percentage)}%
              </p>
            </div>
            <div className="rounded-2xl bg-surface-muted p-4">
              <p className="text-xs font-extrabold uppercase text-foreground/45">
                Niveau
              </p>
              <p className="mt-2 font-bold">{results.level}</p>
            </div>
            <div className="rounded-2xl bg-error/10 p-4 text-error">
              <p className="text-xs font-extrabold uppercase">A renforcer</p>
              <p className="mt-2 font-bold">{results.weakTopics.length}</p>
            </div>
          </div>

          <form
            className="mt-8 space-y-5"
            onSubmit={form.handleSubmit(handleSubmit)}
          >
            <label className="block">
              <span className="font-ui text-xs font-extrabold uppercase text-foreground/55">
                Titre
              </span>
              <input
                className="mt-2 h-14 w-full rounded-2xl border border-border bg-surface-muted px-5 text-sm outline-none transition focus:border-primary"
                placeholder="Plan de remediation IA"
                type="text"
                {...form.register("title")}
              />
            </label>

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="font-ui text-xs font-extrabold uppercase text-foreground/55">
                  Minutes par jour
                </span>
                <input
                  className="mt-2 h-14 w-full rounded-2xl border border-border bg-white px-5 text-sm outline-none transition focus:border-primary"
                  type="number"
                  {...form.register("dailyMinutes")}
                />
              </label>
              <label className="block">
                <span className="font-ui text-xs font-extrabold uppercase text-foreground/55">
                  Date de debut
                </span>
                <input
                  className="mt-2 h-14 w-full rounded-2xl border border-border bg-white px-5 text-sm outline-none transition focus:border-primary"
                  type="date"
                  {...form.register("startDate")}
                />
              </label>
            </div>

            <label className="block">
              <span className="font-ui text-xs font-extrabold uppercase text-foreground/55">
                Intensite
              </span>
              <select
                className="mt-2 h-14 w-full rounded-2xl border border-border bg-white px-5 text-sm font-bold outline-none transition focus:border-primary"
                {...form.register("intensity")}
              >
                <option value="light">Leger</option>
                <option value="balanced">Equilibre</option>
                <option value="intensive">Intensif</option>
              </select>
            </label>

            {generateMutation.isError ? (
              <div className="rounded-2xl border border-error/20 bg-error/5 p-4 text-sm font-semibold text-error">
                Impossible de generer le plan. Verifiez que Gemini est configure
                et que les documents sources sont analyses.
              </div>
            ) : null}

            <button
              className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-primary font-bold text-white shadow-elevated transition hover:bg-secondary disabled:opacity-60"
              disabled={generateMutation.isPending}
              type="submit"
            >
              {generateMutation.isPending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Sparkles className="h-5 w-5" />
              )}
              Generer mon plan
            </button>
          </form>
        </section>

        <section className="rounded-[32px] border border-primary/10 bg-gradient-to-br from-primary/5 to-secondary/5 p-7 shadow-card lg:p-8">
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Donnees analysees
          </p>
          <h2 className="mt-2 font-heading text-3xl font-extrabold">
            {results.assessmentTitle}
          </h2>
          <p className="mt-3 leading-7 text-foreground/60">
            Le plan partira des questions manquees, des feedbacks, des concepts
            manquants et des pages sources.
          </p>

          <div className="mt-6 space-y-3">
            {results.questions.slice(0, 6).map((question) => (
              <article
                className="rounded-2xl border border-primary/10 bg-white p-4"
                key={question.id}
              >
                <div className="flex items-start justify-between gap-4">
                  <p className="font-bold leading-6">{question.text}</p>
                  <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-bold">
                    {question.learnerAnswer.evaluationStatus}
                  </span>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-foreground/55">
                  Source: {question.sourceDocumentTitle}, page{" "}
                  {question.sourcePageNumber}
                </p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
