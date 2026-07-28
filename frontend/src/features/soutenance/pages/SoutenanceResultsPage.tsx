import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Loader2,
  RefreshCcw,
  Sparkles,
  Target,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { cn } from "@/lib/utils";
import { useSoutenanceResults } from "@/features/soutenance/hooks/useSoutenance";
import { type SoutenanceDifficulty } from "@/features/soutenance/types/soutenance";

const difficultyLabels: Record<SoutenanceDifficulty, string> = {
  adaptive: "Adaptatif",
  advanced: "Avance",
  beginner: "Debutant",
  intermediate: "Intermediaire",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function scoreTone(score: number): string {
  if (score >= 75) {
    return "bg-success/10 text-success";
  }
  if (score >= 55) {
    return "bg-warning/15 text-warning";
  }
  return "bg-error/10 text-error";
}

export function SoutenanceResultsPage() {
  const params = useParams();
  const sessionId = Number(params.sessionId);
  const resultsQuery = useSoutenanceResults(
    Number.isFinite(sessionId) ? sessionId : null,
  );

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
          Impossible de charger le rapport de soutenance.
        </div>
      </div>
    );
  }

  const results = resultsQuery.data;

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1280px] space-y-6">
        <section className="rounded-2xl border border-primary/10 bg-white p-6 shadow-card lg:p-8">
          <Link
            className="inline-flex items-center gap-2 text-sm font-bold text-primary"
            to="/soutenance"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour aux simulations
          </Link>

          <div className="mt-7 grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Rapport final
              </p>
              <h1 className="mt-2 font-heading text-4xl font-extrabold">
                {results.title}
              </h1>
              <p className="mt-3 text-foreground/60">
                {difficultyLabels[results.difficulty]} -{" "}
                {formatDate(results.completedAt)}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div
                className={cn(
                  "rounded-2xl p-4 text-center",
                  scoreTone(results.finalScore),
                )}
              >
                <p className="text-xs font-extrabold uppercase">Score</p>
                <p className="mt-2 font-heading text-3xl font-black">
                  {Math.round(results.finalScore)}%
                </p>
              </div>
              <div className="rounded-2xl bg-primary/10 p-4 text-center text-primary sm:col-span-2">
                <p className="text-xs font-extrabold uppercase">Niveau</p>
                <p className="mt-2 font-heading text-xl font-extrabold">
                  {results.readinessLevel}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-3">
          <div className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <p className="flex items-center gap-2 text-xs font-extrabold uppercase text-success">
              <CheckCircle2 className="h-4 w-4" />
              Points acquis
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-foreground/70">
              {results.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <p className="flex items-center gap-2 text-xs font-extrabold uppercase text-error">
              <Target className="h-4 w-4" />
              A renforcer
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-foreground/70">
              {results.weaknesses.concat(results.missingConcepts).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <p className="flex items-center gap-2 text-xs font-extrabold uppercase text-primary">
              <Sparkles className="h-4 w-4" />
              Actions conseillees
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-foreground/70">
              {results.recommendations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-white p-6 shadow-card">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-5 w-5 text-primary" />
            <h2 className="font-heading text-2xl font-extrabold">
              Scores par categorie
            </h2>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {results.categoryScores.map((score) => (
              <div
                className="rounded-xl border border-border bg-surface-muted p-4"
                key={score.category}
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="font-bold">{score.categoryLabel}</p>
                  <span className="font-heading text-xl font-extrabold text-primary">
                    {Math.round(score.score)}%
                  </span>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{ width: `${score.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-5">
          {results.questions.map((item) => (
            <article
              className="rounded-2xl border border-border bg-white p-6 shadow-card"
              key={item.question.id}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="font-ui text-xs font-extrabold uppercase text-primary">
                    Question {item.question.orderIndex + 1} -{" "}
                    {item.question.categoryLabel}
                  </p>
                  <h3 className="mt-2 font-heading text-2xl font-extrabold">
                    {item.question.text}
                  </h3>
                </div>
                <span
                  className={cn(
                    "rounded-full px-4 py-2 text-sm font-extrabold",
                    scoreTone(item.feedback.totalScore),
                  )}
                >
                  {Math.round(item.feedback.totalScore)}%
                </span>
              </div>

              <div className="mt-5 grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl bg-surface-muted p-4">
                  <p className="text-xs font-extrabold uppercase text-foreground/45">
                    Votre reponse
                  </p>
                  <p className="mt-2 leading-7 text-foreground/70">
                    {item.answerText}
                  </p>
                </div>
                <div className="rounded-xl bg-primary/5 p-4">
                  <p className="text-xs font-extrabold uppercase text-primary">
                    Reponse amelioree
                  </p>
                  <p className="mt-2 leading-7 text-foreground/70">
                    {item.feedback.improvedAnswer}
                  </p>
                </div>
              </div>

              <div className="mt-5 grid gap-3 md:grid-cols-2">
                {item.feedback.rubricScores.map((score) => (
                  <div
                    className="rounded-xl border border-border p-4"
                    key={score.criterion}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-extrabold">{score.label}</p>
                      <span className="text-sm font-bold text-primary">
                        {Math.round(score.score)}/100
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-foreground/55">
                      {score.comment}
                    </p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>

        <div className="flex justify-center">
          <Link
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-bold text-white shadow-card transition hover:bg-secondary"
            to="/soutenance"
          >
            <RefreshCcw className="h-4 w-4" />
            Nouvelle simulation
          </Link>
        </div>
      </div>
    </div>
  );
}
