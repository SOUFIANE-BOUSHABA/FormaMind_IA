import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Loader2,
  Mic2,
  Play,
  ShieldQuestion,
  Sparkles,
  Trash2,
} from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  useCreateSoutenanceSession,
  useDeleteSoutenanceSession,
  useSoutenanceSessions,
} from "@/features/soutenance/hooks/useSoutenance";
import {
  type SoutenanceCategory,
  type SoutenanceDifficulty,
  type SoutenanceMode,
  type SoutenanceSessionListItem,
} from "@/features/soutenance/types/soutenance";

const categoryLabels: Record<SoutenanceCategory, string> = {
  ai_concepts: "Concepts IA",
  architecture: "Architecture",
  deployment: "Deploiement",
  jury_challenge: "Defi jury",
  limitations: "Limites",
  project_choices: "Choix projet",
  security: "Securite",
  technical: "Technique",
  testing: "Tests",
};

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

const defaultCategories: SoutenanceCategory[] = [
  "architecture",
  "ai_concepts",
  "technical",
  "project_choices",
  "security",
  "limitations",
];

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

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

function SessionCard({ session }: { session: SoutenanceSessionListItem }) {
  const deleteMutation = useDeleteSoutenanceSession();
  const isCompleted = session.status === "completed";

  return (
    <article className="rounded-2xl border border-border bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-elevated">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            {modeLabels[session.mode]}
          </p>
          <h3 className="mt-2 font-heading text-xl font-extrabold">
            {session.title}
          </h3>
          <p className="mt-1 text-sm text-foreground/55">
            {difficultyLabels[session.difficulty]} - {formatDate(session.createdAt)}
          </p>
        </div>
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-extrabold uppercase",
            isCompleted
              ? "bg-success/10 text-success"
              : "bg-primary/10 text-primary",
          )}
        >
          {isCompleted ? "Terminee" : "En cours"}
        </span>
      </div>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-primary/10">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${session.progressPercentage}%` }}
        />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-foreground/60">
        <span className="rounded-xl bg-surface-muted p-3">
          {session.answeredCount}/{session.questionCount} reponses
        </span>
        <span className="rounded-xl bg-surface-muted p-3">
          {session.finalScore !== null
            ? `${Math.round(session.finalScore)}/100`
            : "Score a venir"}
        </span>
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <Link
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-white shadow-card transition hover:bg-secondary"
          to={
            isCompleted
              ? `/soutenance/${session.id}/results`
              : `/soutenance/${session.id}`
          }
        >
          {isCompleted ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          {isCompleted ? "Voir le rapport" : "Continuer"}
        </Link>
        <button
          className="inline-flex items-center justify-center rounded-xl border border-error/20 px-4 py-3 text-error transition hover:bg-error/5"
          disabled={deleteMutation.isPending}
          onClick={() => {
            deleteMutation.mutate(session.id);
          }}
          type="button"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </article>
  );
}

export function SoutenanceSessionsPage() {
  const navigate = useNavigate();
  const sessionsQuery = useSoutenanceSessions();
  const createMutation = useCreateSoutenanceSession();
  const [title, setTitle] = useState("");
  const [mode, setMode] = useState<SoutenanceMode>("training");
  const [difficulty, setDifficulty] =
    useState<SoutenanceDifficulty>("intermediate");
  const [questionCount, setQuestionCount] = useState(6);
  const [selectedCategories, setSelectedCategories] =
    useState<SoutenanceCategory[]>(defaultCategories);
  const [feedback, setFeedback] = useState<string | null>(null);

  function toggleCategory(category: SoutenanceCategory) {
    setFeedback(null);
    setSelectedCategories((current) => {
      if (current.includes(category)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== category);
      }
      return [...current, category];
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);

    createMutation.mutate(
      {
        difficulty,
        mode,
        questionCategories: selectedCategories,
        questionCount,
        title: title.trim() || null,
      },
      {
        onError: (error) => {
          setFeedback(getErrorMessage(error));
        },
        onSuccess: (session) => {
          navigate(`/soutenance/${session.id}`);
        },
      },
    );
  }

  if (sessionsQuery.isPending) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto grid max-w-[1380px] gap-6 xl:grid-cols-[430px_1fr]">
        <section className="rounded-2xl border border-border bg-white p-5 shadow-card lg:p-6">
          <div className="flex items-center gap-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white">
              <Mic2 className="h-6 w-6" />
            </span>
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Soutenance Coach Agent
              </p>
              <h1 className="font-heading text-2xl font-extrabold">
                Nouvelle simulation
              </h1>
            </div>
          </div>

          <p className="mt-4 leading-7 text-foreground/60">
            Creez une seance de questions/reponses sur le projet FormaMind AI.
            Le coach adapte les questions au profil, puis corrige avec une
            grille de jury.
          </p>

          <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-xs font-bold uppercase text-foreground/50">
                Titre optionnel
              </span>
              <input
                className="mt-2 h-12 w-full rounded-xl border border-border bg-surface-muted px-4 text-sm outline-none focus:border-primary"
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Ex: Soutenance RAG et agents"
                value={title}
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs font-bold uppercase text-foreground/50">
                  Mode
                </span>
                <select
                  className="mt-2 h-12 w-full rounded-xl border border-border bg-white px-3 text-sm font-bold outline-none focus:border-primary"
                  onChange={(event) => setMode(event.target.value as SoutenanceMode)}
                  value={mode}
                >
                  <option value="training">Entrainement</option>
                  <option value="jury">Jury</option>
                </select>
              </label>

              <label className="block">
                <span className="text-xs font-bold uppercase text-foreground/50">
                  Niveau
                </span>
                <select
                  className="mt-2 h-12 w-full rounded-xl border border-border bg-white px-3 text-sm font-bold outline-none focus:border-primary"
                  onChange={(event) =>
                    setDifficulty(event.target.value as SoutenanceDifficulty)
                  }
                  value={difficulty}
                >
                  <option value="beginner">Debutant</option>
                  <option value="intermediate">Intermediaire</option>
                  <option value="advanced">Avance</option>
                  <option value="adaptive">Adaptatif</option>
                </select>
              </label>
            </div>

            <label className="block">
              <span className="text-xs font-bold uppercase text-foreground/50">
                Nombre de questions
              </span>
              <input
                className="mt-2 h-12 w-full rounded-xl border border-border bg-white px-4 text-sm font-bold outline-none focus:border-primary"
                max={20}
                min={3}
                onChange={(event) => setQuestionCount(Number(event.target.value))}
                type="number"
                value={questionCount}
              />
            </label>

            <div>
              <span className="text-xs font-bold uppercase text-foreground/50">
                Axes de questions
              </span>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {(Object.keys(categoryLabels) as SoutenanceCategory[]).map(
                  (category) => (
                    <button
                      className={cn(
                        "rounded-xl border px-3 py-2 text-xs font-bold transition",
                        selectedCategories.includes(category)
                          ? "border-primary bg-primary text-white"
                          : "border-border bg-white text-foreground/65",
                      )}
                      key={category}
                      onClick={() => toggleCategory(category)}
                      type="button"
                    >
                      {categoryLabels[category]}
                    </button>
                  ),
                )}
              </div>
            </div>

            {feedback ? (
              <div className="flex items-start gap-3 rounded-xl border border-error/20 bg-error/5 p-4 text-sm text-error">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                {feedback}
              </div>
            ) : null}

            <button
              className="flex h-14 w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3.5 font-bold text-white shadow-elevated transition hover:bg-secondary disabled:opacity-60"
              disabled={createMutation.isPending}
              type="submit"
            >
              {createMutation.isPending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Sparkles className="h-5 w-5" />
              )}
              Generer la simulation
            </button>
          </form>
        </section>

        <section className="min-h-[680px] rounded-2xl border border-border bg-white p-5 shadow-card lg:p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="font-ui text-xs font-extrabold uppercase text-primary">
                Historique
              </p>
              <h2 className="font-heading text-3xl font-extrabold">
                Simulations de soutenance
              </h2>
            </div>
            <span className="inline-flex items-center gap-2 rounded-xl bg-surface-muted px-4 py-3 text-sm font-bold text-foreground/60">
              <Clock3 className="h-4 w-4 text-primary" />
              {sessionsQuery.data?.total ?? 0} session(s)
            </span>
          </div>

          {sessionsQuery.isError ? (
            <div className="mt-6 rounded-xl border border-error/20 bg-error/5 p-5 text-error">
              Impossible de charger les simulations.
            </div>
          ) : null}

          {sessionsQuery.data?.items.length === 0 ? (
            <div className="mt-10 flex min-h-[480px] items-center justify-center rounded-2xl border border-dashed border-primary/20 bg-surface-muted/50 p-8 text-center">
              <div>
                <span className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <ShieldQuestion className="h-10 w-10" />
                </span>
                <h3 className="mt-5 font-heading text-2xl font-extrabold">
                  Aucune simulation pour le moment
                </h3>
                <p className="mx-auto mt-2 max-w-lg leading-7 text-foreground/60">
                  Lancez une premiere session pour pratiquer les questions de
                  jury sur l'architecture, les agents, le RAG, la securite et
                  les choix techniques.
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-6 grid gap-4 xl:grid-cols-2">
              {sessionsQuery.data?.items.map((session) => (
                <SessionCard key={session.id} session={session} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
