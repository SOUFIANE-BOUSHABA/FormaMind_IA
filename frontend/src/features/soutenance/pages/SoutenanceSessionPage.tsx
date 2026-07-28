import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Mic2,
  Send,
  ShieldQuestion,
  Sparkles,
} from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "@/lib/api-client";
import {
  useCurrentSoutenanceQuestion,
  useSoutenanceSession,
  useSubmitSoutenanceAnswer,
} from "@/features/soutenance/hooks/useSoutenance";
import {
  type SoutenanceAnswerFeedback,
  type SoutenanceDifficulty,
  type SoutenanceMode,
} from "@/features/soutenance/types/soutenance";

const difficultyLabels: Record<SoutenanceDifficulty, string> = {
  adaptive: "Adaptatif",
  advanced: "Avance",
  beginner: "Debutant",
  intermediate: "Intermediaire",
};

const modeLabels: Record<SoutenanceMode, string> = {
  jury: "Mode jury",
  training: "Mode entrainement",
};

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const payload = error.payload as { detail?: string } | null;
    return payload?.detail ?? "Une erreur est survenue.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Une erreur est survenue.";
}

function FeedbackCard({ feedback }: { feedback: SoutenanceAnswerFeedback }) {
  return (
    <section className="rounded-2xl border border-primary/10 bg-white p-5 shadow-card">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Feedback immediat
          </p>
          <h2 className="mt-1 font-heading text-2xl font-extrabold">
            {Math.round(feedback.totalScore)}/100
          </h2>
        </div>
        <span className="rounded-full bg-primary/10 px-4 py-2 text-xs font-bold text-primary">
          Corrige par le coach
        </span>
      </div>

      <p className="mt-4 leading-7 text-foreground/70">{feedback.feedback}</p>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-success/5 p-4">
          <p className="text-xs font-extrabold uppercase text-success">
            Points forts
          </p>
          <ul className="mt-3 space-y-2 text-sm text-foreground/70">
            {feedback.strengths.map((item) => (
              <li className="flex gap-2" key={item}>
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl bg-error/5 p-4">
          <p className="text-xs font-extrabold uppercase text-error">
            A renforcer
          </p>
          <ul className="mt-3 space-y-2 text-sm text-foreground/70">
            {feedback.missingConcepts.map((item) => (
              <li className="flex gap-2" key={item}>
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-error" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-border bg-surface-muted p-4">
        <p className="text-xs font-extrabold uppercase text-primary">
          Reponse amelioree
        </p>
        <p className="mt-2 leading-7 text-foreground/70">
          {feedback.improvedAnswer}
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {feedback.rubricScores.map((score) => (
          <div
            className="rounded-xl border border-border bg-white p-4"
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
    </section>
  );
}

export function SoutenanceSessionPage() {
  const params = useParams();
  const navigate = useNavigate();
  const sessionId = Number(params.sessionId);
  const safeSessionId = Number.isFinite(sessionId) ? sessionId : null;
  const sessionQuery = useSoutenanceSession(safeSessionId);
  const currentQuestionQuery = useCurrentSoutenanceQuestion(safeSessionId);
  const submitMutation = useSubmitSoutenanceAnswer(sessionId);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<SoutenanceAnswerFeedback | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setFeedback(null);

    const question = currentQuestionQuery.data?.question;
    if (!question) {
      setErrorMessage("Aucune question active pour cette simulation.");
      return;
    }

    if (answer.trim().length < 20) {
      setErrorMessage("Votre reponse doit contenir au moins 20 caracteres.");
      return;
    }

    submitMutation.mutate(
      {
        answer: answer.trim(),
        questionId: question.id,
      },
      {
        onError: (error) => {
          setErrorMessage(getErrorMessage(error));
        },
        onSuccess: (response) => {
          setAnswer("");
          setFeedback(response.feedback);
          if (response.status === "completed") {
            navigate(`/soutenance/${response.sessionId}/results`);
          }
        },
      },
    );
  }

  if (sessionQuery.isPending || currentQuestionQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (
    sessionQuery.isError ||
    currentQuestionQuery.isError ||
    !sessionQuery.data ||
    !currentQuestionQuery.data
  ) {
    return (
      <div className="px-4 py-8 pb-28 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger cette simulation.
        </div>
      </div>
    );
  }

  const session = sessionQuery.data;
  const current = currentQuestionQuery.data;
  const question = current.question;

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto grid max-w-[1380px] gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <aside className="space-y-5">
          <section className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <Link
              className="inline-flex items-center gap-2 text-sm font-bold text-primary"
              to="/soutenance"
            >
              <ArrowLeft className="h-4 w-4" />
              Retour aux simulations
            </Link>

            <div className="mt-6 flex items-start gap-4">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white">
                <Mic2 className="h-7 w-7" />
              </span>
              <div>
                <p className="font-ui text-xs font-extrabold uppercase text-primary">
                  Soutenance Coach Agent
                </p>
                <h1 className="mt-1 font-heading text-3xl font-extrabold">
                  {session.title}
                </h1>
                <p className="mt-2 text-sm text-foreground/55">
                  {modeLabels[session.mode]} -{" "}
                  {difficultyLabels[session.difficulty]}
                </p>
              </div>
            </div>

            <p className="mt-5 leading-7 text-foreground/60">
              {session.introduction}
            </p>

            <div className="mt-6">
              <div className="flex items-center justify-between text-sm font-bold">
                <span>Progression</span>
                <span className="text-primary">{current.progressPercentage}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-primary/10">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${current.progressPercentage}%` }}
                />
              </div>
              <p className="mt-2 text-sm text-foreground/55">
                Question {Math.min(current.questionIndex + 1, session.questionCount)}{" "}
                sur {session.questionCount}
              </p>
            </div>
          </section>

          <section className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <p className="font-ui text-xs font-extrabold uppercase text-primary">
              Parcours
            </p>
            <div className="mt-4 space-y-3">
              {session.questions.map((item) => (
                <div
                  className="flex items-center justify-between rounded-xl bg-surface-muted p-3"
                  key={item.id}
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-bold">
                      Question {item.orderIndex + 1}
                    </p>
                    <p className="text-xs text-foreground/55">
                      {item.categoryLabel}
                    </p>
                  </div>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-bold">
                    {item.answerStatus === "answered" ? "Repondue" : "A venir"}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <main className="space-y-5">
          <section className="rounded-2xl border border-primary/10 bg-white p-6 shadow-card lg:p-8">
            {question ? (
              <>
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="font-ui text-xs font-extrabold uppercase text-primary">
                      Question actuelle - {question.categoryLabel}
                    </p>
                    <h2 className="mt-3 font-heading text-3xl font-extrabold leading-tight">
                      {question.text}
                    </h2>
                  </div>
                  <span className="w-fit rounded-full bg-primary/10 px-4 py-2 text-xs font-extrabold uppercase text-primary">
                    {difficultyLabels[question.difficulty]}
                  </span>
                </div>

                <form className="mt-7 space-y-4" onSubmit={handleSubmit}>
                  <label className="block">
                    <span className="text-xs font-bold uppercase text-foreground/50">
                      Votre reponse orale transcrite
                    </span>
                    <textarea
                      className="mt-2 min-h-[220px] w-full resize-y rounded-2xl border border-border bg-surface-muted p-5 text-sm leading-7 outline-none transition focus:border-primary"
                      onChange={(event) => setAnswer(event.target.value)}
                      placeholder="Expliquez votre raisonnement comme devant le jury..."
                      value={answer}
                    />
                  </label>

                  {errorMessage ? (
                    <div className="flex items-start gap-3 rounded-xl border border-error/20 bg-error/5 p-4 text-sm text-error">
                      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                      {errorMessage}
                    </div>
                  ) : null}

                  <button
                    className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-primary font-bold text-white shadow-elevated transition hover:bg-secondary disabled:opacity-60"
                    disabled={submitMutation.isPending}
                    type="submit"
                  >
                    {submitMutation.isPending ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                    Envoyer au coach
                  </button>
                </form>
              </>
            ) : (
              <div className="flex min-h-[420px] items-center justify-center text-center">
                <div>
                  <span className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <ShieldQuestion className="h-10 w-10" />
                  </span>
                  <h2 className="mt-5 font-heading text-2xl font-extrabold">
                    Simulation terminee
                  </h2>
                  <Link
                    className="mt-6 inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 font-bold text-white"
                    to={`/soutenance/${session.id}/results`}
                  >
                    Voir le rapport
                  </Link>
                </div>
              </div>
            )}
          </section>

          {feedback ? <FeedbackCard feedback={feedback} /> : null}

          {session.mode === "jury" && !feedback ? (
            <section className="rounded-2xl border border-primary/10 bg-primary/5 p-5">
              <div className="flex items-start gap-3">
                <Sparkles className="mt-0.5 h-5 w-5 text-primary" />
                <p className="text-sm leading-6 text-foreground/65">
                  En mode jury, le feedback detaille est cache pendant la
                  simulation et apparait dans le rapport final.
                </p>
              </div>
            </section>
          ) : null}
        </main>
      </div>
    </div>
  );
}
