import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileText,
  Loader2,
  Plus,
  ShieldQuestion,
  Sparkles,
  Target,
} from "lucide-react";
import { type FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  useAssessment,
  useAssessmentAttempts,
  useAssessments,
  useGenerateAssessment,
  useStartAssessmentAttempt,
} from "@/features/assessments/hooks/useAssessments";
import {
  type AssessmentDifficulty,
  type AssessmentItem,
  type QuestionType,
} from "@/features/assessments/types/assessments";
import { useDocuments } from "@/features/documents/hooks/useDocuments";
import { type DocumentItem } from "@/features/documents/types/documents";

const difficultyLabels: Record<AssessmentDifficulty, string> = {
  adaptive: "Adaptatif",
  advanced: "Avance",
  beginner: "Debutant",
  intermediate: "Intermediaire",
};

const questionTypeLabels: Record<QuestionType, string> = {
  explanation: "Explication",
  multiple_choice: "QCM",
  short_answer: "Reponse courte",
  true_false: "Vrai / Faux",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

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

function AssessmentsSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
      <div className="h-[720px] animate-pulse rounded-2xl bg-white" />
      <div className="h-[720px] animate-pulse rounded-2xl bg-white" />
    </div>
  );
}

type DocumentSelectorProps = {
  documents: DocumentItem[];
  selectedIds: number[];
  onToggle: (documentId: number) => void;
};

function DocumentSelector({
  documents,
  selectedIds,
  onToggle,
}: DocumentSelectorProps) {
  return (
    <div className="space-y-3">
      {documents.map((document) => {
        const isSelected = selectedIds.includes(document.id);
        return (
          <button
            className={cn(
              "flex w-full items-center gap-3 rounded-xl border p-3 text-left transition",
              isSelected
                ? "border-primary bg-primary/5 shadow-card"
                : "border-border bg-white hover:border-primary/30",
            )}
            key={document.id}
            onClick={() => onToggle(document.id)}
            type="button"
          >
            <span
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                isSelected ? "bg-primary text-white" : "bg-surface-muted text-primary",
              )}
            >
              {isSelected ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : (
                <FileText className="h-5 w-5" />
              )}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-extrabold">
                {document.title}
              </span>
              <span className="text-xs text-foreground/55">
                {document.pageCount} pages
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

type ResultPanelProps = {
  assessment: AssessmentItem | undefined;
  isLoading: boolean;
  onStart: (assessmentId: number) => void;
  isStarting: boolean;
};

function ResultPanel({
  assessment,
  isLoading,
  isStarting,
  onStart,
}: ResultPanelProps) {
  if (isLoading) {
    return (
      <section className="min-h-[640px] rounded-2xl border border-border bg-white p-6 shadow-card">
        <div className="h-full animate-pulse rounded-xl bg-primary/10" />
      </section>
    );
  }

  if (!assessment) {
    return (
      <section className="flex min-h-[640px] items-center justify-center rounded-2xl border border-border bg-white p-8 text-center shadow-card">
        <div>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldQuestion className="h-8 w-8" />
          </div>
          <h2 className="mt-5 font-heading text-2xl font-extrabold">
            Generez une premiere evaluation
          </h2>
          <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-foreground/60">
            Selectionnez un document pret, choisissez les sujets, puis laissez
            l'agent creer des questions sourcees.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <div className="flex flex-col gap-4 border-b border-border pb-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Evaluation generee
          </p>
          <h2 className="mt-1 font-heading text-3xl font-extrabold">
            {assessment.title}
          </h2>
          <p className="mt-2 text-sm text-foreground/55">
            {difficultyLabels[assessment.difficulty]} ·{" "}
            {assessment.questionCount} question(s) ·{" "}
            {formatDate(assessment.createdAt)}
          </p>
        </div>
        <div className="rounded-xl bg-primary/10 px-4 py-3 text-sm font-bold text-primary">
          {assessment.documents.map((document) => document.title).join(", ")}
        </div>
      </div>

      <button
        className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3.5 font-ui text-sm font-bold text-white shadow-card transition hover:bg-secondary disabled:opacity-60 sm:w-auto"
        disabled={isStarting}
        onClick={() => onStart(assessment.id)}
        type="button"
      >
        {isStarting ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <ShieldQuestion className="h-5 w-5" />
        )}
        Commencer l'evaluation
      </button>

      <div className="mt-6 space-y-4">
        {assessment.questions.map((question, index) => (
          <article
            className="rounded-2xl border border-border bg-surface-muted/40 p-5"
            key={question.id}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-xs font-extrabold uppercase text-primary">
                  Question {index + 1} · {questionTypeLabels[question.type]}
                </p>
                <h3 className="mt-2 font-heading text-xl font-extrabold">
                  {question.text}
                </h3>
              </div>
              <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-foreground/60">
                {question.points} pt
              </span>
            </div>

            {question.options.length > 0 ? (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {question.options.map((option) => (
                  <div
                    className="rounded-xl border border-border bg-white px-4 py-3 text-sm font-semibold"
                    key={option.id}
                  >
                    {option.text}
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mt-4 rounded-xl border border-primary/10 bg-white p-4 text-xs leading-6 text-foreground/60">
              <p className="font-extrabold text-primary">
                Source: {question.sourceDocumentTitle}, page{" "}
                {question.sourcePageNumber}
              </p>
              <p className="mt-1 line-clamp-3">{question.sourceExcerpt}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function AssessmentsPage() {
  const navigate = useNavigate();
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [title, setTitle] = useState("");
  const [topics, setTopics] = useState("RAG, comprehension");
  const [difficulty, setDifficulty] =
    useState<AssessmentDifficulty>("intermediate");
  const [questionCount, setQuestionCount] = useState(5);
  const [questionTypes, setQuestionTypes] = useState<QuestionType[]>([
    "multiple_choice",
  ]);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<number | null>(
    null,
  );
  const [page, setPage] = useState(1);
  const [feedback, setFeedback] = useState<string | null>(null);

  const readyDocumentsQuery = useDocuments(
    useMemo(
      () => ({
        page: 1,
        pageSize: 50,
        sort: "newest",
        status: "ready" as const,
      }),
      [],
    ),
  );
  const assessmentsQuery = useAssessments(
    useMemo(
      () => ({
        page,
        pageSize: 6,
        sort: "newest" as const,
      }),
      [page],
    ),
  );
  const selectedAssessmentQuery = useAssessment(selectedAssessmentId);
  const attemptsQuery = useAssessmentAttempts(selectedAssessmentId);
  const generateMutation = useGenerateAssessment();
  const startAttemptMutation = useStartAssessmentAttempt();

  const readyDocuments = readyDocumentsQuery.data?.items ?? [];
  const selectedAssessment =
    selectedAssessmentQuery.data ?? generateMutation.data ?? undefined;
  const totalPages = assessmentsQuery.data?.totalPages ?? 0;

  function toggleDocument(documentId: number) {
    setFeedback(null);
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  }

  function toggleQuestionType(questionType: QuestionType) {
    setQuestionTypes((current) => {
      if (current.includes(questionType)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== questionType);
      }

      return [...current, questionType];
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    const cleanedTopics = topics
      .split(",")
      .map((topic) => topic.trim())
      .filter(Boolean);

    if (selectedDocumentIds.length === 0) {
      setFeedback("Selectionnez au moins un document pret.");
      return;
    }

    if (cleanedTopics.length === 0) {
      setFeedback("Ajoutez au moins un sujet.");
      return;
    }

    generateMutation.mutate(
      {
        difficulty,
        documentIds: selectedDocumentIds,
        questionCount,
        questionTypes,
        title: title.trim() || undefined,
        topics: cleanedTopics.slice(0, 5),
      },
      {
        onError: (error) => {
          setFeedback(getErrorMessage(error));
        },
        onSuccess: (assessment) => {
          setSelectedAssessmentId(assessment.id);
        },
      },
    );
  }

  function handleStartAssessment(assessmentId: number) {
    setFeedback(null);
    startAttemptMutation.mutate(assessmentId, {
      onError: (error) => {
        setFeedback(getErrorMessage(error));
      },
      onSuccess: (attempt) => {
        navigate(`/attempts/${attempt.id}`);
      },
    });
  }

  if (readyDocumentsQuery.isPending) {
    return (
      <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
        <AssessmentsSkeleton />
      </div>
    );
  }

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1440px] space-y-8">
        <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-heading text-4xl font-extrabold tracking-normal text-foreground lg:text-5xl">
              Evaluations
            </h1>
            <p className="mt-2 max-w-2xl text-foreground/65">
              Creez des quiz sourcees depuis vos supports analyses avec l'agent
              pedagogique FormaMind.
            </p>
          </div>
         
        </section>

        <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
          <aside className="space-y-6">
            <form
              className="rounded-2xl border border-border bg-white p-5 shadow-card"
              onSubmit={handleSubmit}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white">
                  <Target className="h-6 w-6" />
                </div>
                <div>
                  <p className="font-ui text-xs font-extrabold uppercase text-primary">
                    Generation
                  </p>
                  <h2 className="font-heading text-xl font-extrabold">
                    Nouvelle evaluation
                  </h2>
                </div>
              </div>

              <div className="mt-5 space-y-4">
                <label className="block">
                  <span className="text-xs font-bold uppercase text-foreground/50">
                    Titre optionnel
                  </span>
                  <input
                    className="mt-2 h-11 w-full rounded-xl border border-border bg-surface-muted px-4 text-sm outline-none focus:border-primary"
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder="Ex: Quiz RAG niveau 1"
                    value={title}
                  />
                </label>

                <label className="block">
                  <span className="text-xs font-bold uppercase text-foreground/50">
                    Sujets
                  </span>
                  <input
                    className="mt-2 h-11 w-full rounded-xl border border-border bg-surface-muted px-4 text-sm outline-none focus:border-primary"
                    onChange={(event) => setTopics(event.target.value)}
                    placeholder="RAG, embeddings, retrieval"
                    value={topics}
                  />
                </label>

                <div className="grid grid-cols-2 gap-3">
                  <label className="block">
                    <span className="text-xs font-bold uppercase text-foreground/50">
                      Niveau
                    </span>
                    <select
                      className="mt-2 h-11 w-full rounded-xl border border-border bg-white px-3 text-sm font-semibold outline-none focus:border-primary"
                      onChange={(event) =>
                        setDifficulty(event.target.value as AssessmentDifficulty)
                      }
                      value={difficulty}
                    >
                      <option value="beginner">Debutant</option>
                      <option value="intermediate">Intermediaire</option>
                      <option value="advanced">Avance</option>
                      <option value="adaptive">Adaptatif</option>
                    </select>
                  </label>

                  <label className="block">
                    <span className="text-xs font-bold uppercase text-foreground/50">
                      Questions
                    </span>
                    <input
                      className="mt-2 h-11 w-full rounded-xl border border-border bg-white px-3 text-sm font-semibold outline-none focus:border-primary"
                      max={20}
                      min={3}
                      onChange={(event) =>
                        setQuestionCount(Number(event.target.value))
                      }
                      type="number"
                      value={questionCount}
                    />
                  </label>
                </div>

                <div>
                  <span className="text-xs font-bold uppercase text-foreground/50">
                    Types
                  </span>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    {(Object.keys(questionTypeLabels) as QuestionType[]).map(
                      (questionType) => (
                        <button
                          className={cn(
                            "rounded-xl border px-3 py-2 text-xs font-bold transition",
                            questionTypes.includes(questionType)
                              ? "border-primary bg-primary text-white"
                              : "border-border bg-white text-foreground/65",
                          )}
                          key={questionType}
                          onClick={() => toggleQuestionType(questionType)}
                          type="button"
                        >
                          {questionTypeLabels[questionType]}
                        </button>
                      ),
                    )}
                  </div>
                </div>

                {readyDocuments.length > 0 ? (
                  <div>
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase text-foreground/50">
                        Documents prets
                      </span>
                      <span className="rounded-full bg-primary/10 px-2 py-1 text-xs font-bold text-primary">
                        {selectedDocumentIds.length}/{readyDocuments.length}
                      </span>
                    </div>
                    <DocumentSelector
                      documents={readyDocuments}
                      onToggle={toggleDocument}
                      selectedIds={selectedDocumentIds}
                    />
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-border bg-surface-muted p-5 text-center text-sm text-foreground/60">
                    Aucun document pret. Analysez un PDF avant de generer une
                    evaluation.
                    <Link
                      className="mt-3 inline-flex items-center gap-2 font-bold text-primary"
                      to="/documents"
                    >
                      <Plus className="h-4 w-4" />
                      Preparer un document
                    </Link>
                  </div>
                )}

                {feedback ? (
                  <div className="flex items-start gap-3 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    {feedback}
                  </div>
                ) : null}

                <button
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3.5 font-ui text-sm font-bold text-white shadow-card transition hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={generateMutation.isPending || readyDocuments.length === 0}
                  type="submit"
                >
                  {generateMutation.isPending ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Sparkles className="h-5 w-5" />
                  )}
                  Generer l'evaluation
                </button>
              </div>
            </form>

            <section className="rounded-2xl border border-border bg-white p-5 shadow-card">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-ui text-xs font-extrabold uppercase text-primary">
                    Historique
                  </p>
                  <h2 className="font-heading text-xl font-extrabold">
                    Evaluations recentes
                  </h2>
                </div>
              </div>

              {assessmentsQuery.isLoading ? (
                <div className="mt-5 space-y-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div
                      className="h-20 animate-pulse rounded-xl bg-primary/10"
                      key={index}
                    />
                  ))}
                </div>
              ) : null}

              {assessmentsQuery.data?.items.length === 0 ? (
                <p className="mt-5 rounded-xl border border-dashed border-border bg-surface-muted p-4 text-sm text-foreground/55">
                  Aucune evaluation generee pour le moment.
                </p>
              ) : null}

              <div className="mt-5 space-y-3">
                {assessmentsQuery.data?.items.map((assessment) => (
                  <button
                    className={cn(
                      "w-full rounded-xl border p-4 text-left transition",
                      selectedAssessmentId === assessment.id
                        ? "border-primary bg-primary/5"
                        : "border-border bg-white hover:border-primary/30",
                    )}
                    key={assessment.id}
                    onClick={() => setSelectedAssessmentId(assessment.id)}
                    type="button"
                  >
                    <p className="font-heading text-base font-extrabold">
                      {assessment.title}
                    </p>
                    <p className="mt-1 text-xs text-foreground/55">
                      {assessment.questionCount} question(s) ·{" "}
                      {formatDate(assessment.createdAt)}
                    </p>
                  </button>
                ))}
              </div>

              {totalPages > 1 ? (
                <div className="mt-4 flex items-center justify-end gap-2">
                  <button
                    aria-label="Page precedente"
                    className="rounded-lg border border-border p-2 disabled:opacity-40"
                    disabled={page <= 1}
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    type="button"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button
                    aria-label="Page suivante"
                    className="rounded-lg border border-border p-2 disabled:opacity-40"
                    disabled={page >= totalPages}
                    onClick={() => setPage((current) => current + 1)}
                    type="button"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              ) : null}
            </section>

            {selectedAssessmentId !== null ? (
              <section className="rounded-2xl border border-border bg-white p-5 shadow-card">
                <p className="font-ui text-xs font-extrabold uppercase text-primary">
                  Tentatives
                </p>
                {attemptsQuery.data?.items.length === 0 ? (
                  <p className="mt-3 text-sm text-foreground/55">
                    Aucune tentative pour cette evaluation.
                  </p>
                ) : null}
                <div className="mt-4 space-y-3">
                  {attemptsQuery.data?.items.map((attempt) => (
                    <Link
                      className="block rounded-xl border border-border bg-surface-muted p-4 text-sm font-bold transition hover:border-primary/30"
                      key={attempt.id}
                      to={
                        attempt.status === "evaluated"
                          ? `/attempts/${attempt.id}/results`
                          : `/attempts/${attempt.id}`
                      }
                    >
                      Tentative #{attempt.id} · {attempt.status}
                      {attempt.percentage !== null ? (
                        <span className="mt-1 block text-primary">
                          {Math.round(attempt.percentage)}/100
                        </span>
                      ) : null}
                    </Link>
                  ))}
                </div>
              </section>
            ) : null}
          </aside>

          <ResultPanel
            assessment={selectedAssessment}
            isLoading={selectedAssessmentQuery.isLoading}
            isStarting={startAttemptMutation.isPending}
            onStart={handleStartAssessment}
          />
        </div>
      </div>
    </div>
  );
}
