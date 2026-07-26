import {
  Award,
  BookOpenCheck,
  CheckCircle2,
  Map,
  FileText,
  Loader2,
  Sparkles,
  Target,
  XCircle,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { cn } from "@/lib/utils";
import { useAttemptResults } from "@/features/assessments/hooks/useAssessments";
import {
  type AssessmentCoachFeedback,
  type ResultQuestion,
} from "@/features/assessments/types/attempts";

function statusLabel(status: ResultQuestion["learnerAnswer"]["evaluationStatus"]) {
  if (status === "correct") {
    return "Correct";
  }
  if (status === "partial") {
    return "Partiel";
  }
  if (status === "unanswered") {
    return "Sans reponse";
  }
  return "Incorrect";
}

function masteryLabel(level: AssessmentCoachFeedback["masteryLevel"]) {
  if (level === "strong") {
    return "Maitrise forte";
  }
  if (level === "medium") {
    return "Maitrise partielle";
  }
  return "A renforcer";
}

function CoachFeedbackPanel({
  feedback,
}: {
  feedback: AssessmentCoachFeedback;
}) {
  return (
    <section className="rounded-2xl border border-primary/10 bg-white p-6 shadow-card">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Coach pedagogique
          </p>
          <h2 className="mt-2 font-heading text-3xl font-extrabold">
            {masteryLabel(feedback.masteryLevel)}
          </h2>
          <p className="mt-3 max-w-3xl leading-7 text-foreground/65">
            {feedback.summary}
          </p>
        </div>
        <div className="rounded-full bg-primary/10 px-5 py-3 text-sm font-extrabold text-primary">
          Confiance {feedback.confidence}
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="rounded-xl border border-error/15 bg-error/5 p-4">
          <Target className="h-5 w-5 text-error" />
          <p className="mt-3 text-xs font-extrabold uppercase text-error">
            Points a renforcer
          </p>
          <ul className="mt-3 space-y-2 text-sm font-semibold leading-6">
            {(feedback.pointsARenforcer.length
              ? feedback.pointsARenforcer
              : ["Aucun point faible majeur detecte."]).map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-success/15 bg-success/5 p-4">
          <BookOpenCheck className="h-5 w-5 text-success" />
          <p className="mt-3 text-xs font-extrabold uppercase text-success">
            Points acquis
          </p>
          <ul className="mt-3 space-y-2 text-sm font-semibold leading-6">
            {(feedback.pointsAcquis.length
              ? feedback.pointsAcquis
              : ["Aucun acquis confirme pour cette tentative."]).map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl border border-primary/10 bg-primary/5 p-4">
          <Sparkles className="h-5 w-5 text-primary" />
          <p className="mt-3 text-xs font-extrabold uppercase text-primary">
            Actions conseillees
          </p>
          <ul className="mt-3 space-y-2 text-sm font-semibold leading-6">
            {feedback.recommendedActions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </div>
      </div>

      {feedback.recommendedSources.length > 0 ? (
        <div className="mt-5 rounded-xl border border-border bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Sources recommandees
          </p>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {feedback.recommendedSources.map((source) => (
              <div
                className="rounded-xl bg-white p-4 text-sm leading-6"
                key={`${source.documentId}-${source.pageNumber}-${source.excerpt}`}
              >
                <p className="font-extrabold text-primary">
                  {source.documentTitle}, page {source.pageNumber}
                </p>
                <p className="mt-2 text-foreground/60">{source.reason}</p>
                <p className="mt-2 line-clamp-3 text-foreground/50">
                  {source.excerpt}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function QuestionResultCard({ question }: { question: ResultQuestion }) {
  const answer = question.learnerAnswer;
  const isGood = answer.evaluationStatus === "correct";

  return (
    <article className="rounded-2xl border border-border bg-white p-5 shadow-card">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Question {question.orderIndex + 1} · {question.type}
          </p>
          <h2 className="mt-2 font-heading text-2xl font-extrabold">
            {question.text}
          </h2>
        </div>
        <span
          className={cn(
            "rounded-full px-4 py-2 text-sm font-extrabold",
            isGood ? "bg-success/10 text-success" : "bg-error/10 text-error",
          )}
        >
          {answer.pointsAwarded ?? 0}/{question.points} pt
        </span>
      </div>

      {question.options.length > 0 ? (
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {question.options.map((option) => {
            const selected = answer.selectedOptionId === option.id;
            return (
              <div
                className={cn(
                  "rounded-xl border p-4 text-sm font-semibold",
                  option.isCorrect
                    ? "border-success/30 bg-success/10 text-success"
                    : selected
                      ? "border-error/30 bg-error/10 text-error"
                      : "border-border bg-surface-muted",
                )}
                key={option.id}
              >
                {option.text}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mt-5 rounded-xl border border-border bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Votre reponse
          </p>
          <p className="mt-2 leading-7">
            {answer.textAnswer || "Aucune reponse fournie."}
          </p>
        </div>
      )}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-primary/10 bg-primary/5 p-4">
          <p className="text-xs font-extrabold uppercase text-primary">
            Feedback
          </p>
          <p className="mt-2 text-sm leading-6">
            {statusLabel(answer.evaluationStatus)} · {answer.feedback}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-surface-muted p-4">
          <p className="text-xs font-extrabold uppercase text-foreground/45">
            Reponse attendue
          </p>
          <p className="mt-2 text-sm leading-6">{question.correctAnswer}</p>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-border bg-white p-4 text-sm text-foreground/60">
        <p className="font-extrabold text-primary">
          Source: {question.sourceDocumentTitle}, page {question.sourcePageNumber}
        </p>
        <p className="mt-2 line-clamp-3">{question.sourceExcerpt}</p>
      </div>
    </article>
  );
}

export function ResultsPage() {
  const params = useParams();
  const attemptId = Number(params.attemptId);
  const resultsQuery = useAttemptResults(Number.isFinite(attemptId) ? attemptId : null);

  if (resultsQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (resultsQuery.isError || !resultsQuery.data) {
    return (
      <div className="px-4 py-8 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger les resultats.
        </div>
      </div>
    );
  }

  const results = resultsQuery.data;

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1180px] space-y-6">
        <section className="rounded-2xl border border-primary/10 bg-white p-8 shadow-card">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Resultats d'evaluation
              </p>
              <h1 className="mt-2 font-heading text-4xl font-extrabold">
                {results.assessmentTitle}
              </h1>
              <p className="mt-2 text-foreground/60">
                Niveau {results.level} · Score final persiste
              </p>
            </div>
            <div className="flex h-36 w-36 flex-col items-center justify-center rounded-full bg-primary text-white shadow-elevated">
              <Award className="h-8 w-8" />
              <span className="mt-2 font-heading text-4xl font-black">
                {Math.round(results.percentage)}
              </span>
              <span className="text-xs font-bold">/100</span>
            </div>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className="rounded-xl bg-surface-muted p-4">
              <p className="text-xs font-bold uppercase text-foreground/45">
                Points
              </p>
              <p className="mt-1 text-2xl font-extrabold">
                {results.score}/{results.maxScore}
              </p>
            </div>
            <div className="rounded-xl bg-success/10 p-4 text-success">
              <CheckCircle2 className="h-5 w-5" />
              <p className="mt-2 text-sm font-bold">
                {results.strongTopics.join(", ") || "Aucun point fort encore"}
              </p>
            </div>
            <div className="rounded-xl bg-error/10 p-4 text-error">
              <XCircle className="h-5 w-5" />
              <p className="mt-2 text-sm font-bold">
                {results.weakTopics.join(", ") || "Aucun point faible majeur"}
              </p>
            </div>
          </div>
          <Link
            className="mt-6 inline-flex items-center gap-2 font-bold text-primary"
            to="/assessments"
          >
            <FileText className="h-5 w-5" />
            Retour aux evaluations
          </Link>
          <Link
            className="ml-0 mt-4 inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 font-bold text-white shadow-elevated transition hover:bg-secondary sm:ml-4"
            to={`/learning-plans/new/${results.id}`}
          >
            <Map className="h-5 w-5" />
            Generer mon plan d'apprentissage
          </Link>
        </section>

        {results.coachFeedback ? (
          <CoachFeedbackPanel feedback={results.coachFeedback} />
        ) : null}

        <section className="space-y-4">
          {results.questions.map((question) => (
            <QuestionResultCard key={question.id} question={question} />
          ))}
        </section>
      </div>
    </div>
  );
}
