import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Flag,
  Loader2,
  Send,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { cn } from "@/lib/utils";
import {
  useAttempt,
  useSaveAttemptAnswer,
  useSubmitAttempt,
} from "@/features/assessments/hooks/useAssessments";
import {
  type AttemptAnswer,
  type AttemptQuestion,
} from "@/features/assessments/types/attempts";

function answerFor(
  answers: AttemptAnswer[],
  questionId: number,
): AttemptAnswer | undefined {
  return answers.find((answer) => answer.questionId === questionId);
}

export function QuizPage() {
  const params = useParams();
  const navigate = useNavigate();
  const attemptId = Number(params.attemptId);
  const attemptQuery = useAttempt(Number.isFinite(attemptId) ? attemptId : null);
  const saveMutation = useSaveAttemptAnswer(attemptId);
  const submitMutation = useSubmitAttempt(attemptId);
  const [activeIndex, setActiveIndex] = useState(0);
  const [draftText, setDraftText] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  const attempt = attemptQuery.data;
  const activeQuestion = attempt?.questions[activeIndex];
  const activeAnswer =
    attempt && activeQuestion
      ? answerFor(attempt.answers, activeQuestion.id)
      : undefined;

  const answeredQuestionIds = useMemo(
    () =>
      new Set(
        attempt?.answers
          .filter(
            (answer) =>
              answer.selectedOptionId !== null || Boolean(answer.textAnswer),
          )
          .map((answer) => answer.questionId) ?? [],
      ),
    [attempt?.answers],
  );

  function saveAnswer(
    question: AttemptQuestion,
    input: {
      selectedOptionId?: number | null;
      textAnswer?: string | null;
      isFlagged?: boolean;
    },
  ) {
    setError(null);
    saveMutation.mutate(
      {
        input: {
          isFlagged: input.isFlagged ?? activeAnswer?.isFlagged ?? false,
          selectedOptionId: input.selectedOptionId ?? null,
          textAnswer: input.textAnswer ?? null,
        },
        questionId: question.id,
      },
      {
        onError: () => {
          setError("Impossible d'enregistrer votre reponse.");
        },
      },
    );
  }

  function handleSubmit() {
    if (!window.confirm("Soumettre cette evaluation pour correction ?")) {
      return;
    }

    setError(null);
    submitMutation.mutate(undefined, {
      onError: () => {
        setError("Impossible de soumettre l'evaluation.");
      },
      onSuccess: (results) => {
        navigate(`/attempts/${results.id}/results`, { replace: true });
      },
    });
  }

  if (attemptQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (attemptQuery.isError || !attempt || !activeQuestion) {
    return (
      <div className="px-4 py-8 lg:px-10">
        <div className="rounded-2xl border border-error/20 bg-white p-8 text-error">
          Impossible de charger cette tentative.
        </div>
      </div>
    );
  }

  const isOpenQuestion =
    activeQuestion.type === "short_answer" ||
    activeQuestion.type === "explanation";
  const currentText =
    draftText[activeQuestion.id] ?? activeAnswer?.textAnswer ?? "";

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto grid max-w-[1440px] gap-6 xl:grid-cols-[320px_1fr]">
        <aside className="rounded-2xl border border-border bg-white p-5 shadow-card">
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Tentative en cours
          </p>
          <h1 className="mt-2 font-heading text-xl font-extrabold">
            {attempt.assessmentTitle}
          </h1>
          <p className="mt-2 text-sm text-foreground/55">
            {attempt.answeredCount}/{attempt.totalQuestions} reponses ·{" "}
            {attempt.flaggedCount} a revoir
          </p>
          <div className="mt-5 grid grid-cols-5 gap-2 xl:grid-cols-4">
            {attempt.questions.map((question, index) => (
              <button
                className={cn(
                  "h-11 rounded-xl border text-sm font-extrabold transition",
                  activeIndex === index
                    ? "border-primary bg-primary text-white"
                    : answeredQuestionIds.has(question.id)
                      ? "border-success/30 bg-success/10 text-success"
                      : "border-border bg-surface-muted text-foreground/60",
                )}
                key={question.id}
                onClick={() => setActiveIndex(index)}
                type="button"
              >
                {index + 1}
              </button>
            ))}
          </div>
          <button
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 font-bold text-white shadow-card disabled:opacity-60"
            disabled={submitMutation.isPending}
            onClick={handleSubmit}
            type="button"
          >
            {submitMutation.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
            Soumettre
          </button>
        </aside>

        <main className="rounded-2xl border border-border bg-white p-6 shadow-card lg:p-8">
          <div className="flex flex-col gap-4 border-b border-border pb-6 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Question {activeIndex + 1} · {activeQuestion.type}
              </p>
              <h2 className="mt-3 max-w-4xl font-heading text-3xl font-extrabold">
                {activeQuestion.text}
              </h2>
            </div>
            <span className="rounded-full bg-primary/10 px-4 py-2 text-sm font-bold text-primary">
              {activeQuestion.points} pt
            </span>
          </div>

          <section className="mt-8">
            {isOpenQuestion ? (
              <div className="space-y-4">
                <textarea
                  className="min-h-56 w-full resize-y rounded-2xl border border-border bg-surface-muted p-4 text-base leading-7 outline-none focus:border-primary"
                  onChange={(event) =>
                    setDraftText((current) => ({
                      ...current,
                      [activeQuestion.id]: event.target.value,
                    }))
                  }
                  placeholder="Redigez votre reponse ici..."
                  value={currentText}
                />
                <button
                  className="rounded-xl bg-primary px-5 py-3 font-bold text-white shadow-card disabled:opacity-60"
                  disabled={saveMutation.isPending}
                  onClick={() =>
                    saveAnswer(activeQuestion, {
                      isFlagged: activeAnswer?.isFlagged,
                      textAnswer: currentText,
                    })
                  }
                  type="button"
                >
                  Enregistrer la reponse
                </button>
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {activeQuestion.options.map((option) => {
                  const selected = activeAnswer?.selectedOptionId === option.id;
                  return (
                    <button
                      className={cn(
                        "rounded-2xl border p-5 text-left font-semibold transition",
                        selected
                          ? "border-primary bg-primary/10 text-primary"
                          : "border-border bg-surface-muted hover:border-primary/40",
                      )}
                      key={option.id}
                      onClick={() =>
                        saveAnswer(activeQuestion, {
                          isFlagged: activeAnswer?.isFlagged,
                          selectedOptionId: option.id,
                        })
                      }
                      type="button"
                    >
                      {option.text}
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          <div className="mt-8 flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
            <button
              className={cn(
                "flex items-center gap-2 rounded-xl border px-4 py-3 font-bold",
                activeAnswer?.isFlagged
                  ? "border-warning bg-warning/10 text-warning"
                  : "border-border text-foreground/60",
              )}
              onClick={() =>
                saveAnswer(activeQuestion, {
                  isFlagged: !activeAnswer?.isFlagged,
                  selectedOptionId: activeAnswer?.selectedOptionId,
                  textAnswer: currentText || activeAnswer?.textAnswer,
                })
              }
              type="button"
            >
              <Flag className="h-5 w-5" />
              Marquer a revoir
            </button>

            <div className="flex items-center justify-between gap-3">
              {saveMutation.isSuccess ? (
                <span className="flex items-center gap-2 text-sm font-bold text-success">
                  <CheckCircle2 className="h-4 w-4" />
                  Enregistre
                </span>
              ) : null}
              {error ? (
                <span className="flex items-center gap-2 text-sm font-bold text-error">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </span>
              ) : null}
              <button
                className="rounded-xl border border-border p-3 disabled:opacity-40"
                disabled={activeIndex === 0}
                onClick={() => setActiveIndex((current) => current - 1)}
                type="button"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                className="rounded-xl border border-border p-3 disabled:opacity-40"
                disabled={activeIndex === attempt.questions.length - 1}
                onClick={() => setActiveIndex((current) => current + 1)}
                type="button"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
