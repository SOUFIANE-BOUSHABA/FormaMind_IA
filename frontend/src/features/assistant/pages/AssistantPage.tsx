import {
  AlertCircle,
  Bot,
  CheckCircle2,
  FileText,
  Loader2,
  MessageCircleQuestion,
  Plus,
  Send,
  Sparkles,
} from "lucide-react";
import { type FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import { useAskAssistant } from "@/features/assistant/hooks/useAssistant";
import { type AssistantMessage } from "@/features/assistant/types/assistant";
import { useDocuments } from "@/features/documents/hooks/useDocuments";
import { type DocumentItem } from "@/features/documents/types/documents";

type AssistantLocationState = {
  selectedDocumentId?: number;
};

function createMessageId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
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

function AssistantSkeleton() {
  return (
    <div className="grid gap-6 px-4 py-8 pb-28 lg:grid-cols-[320px_1fr] lg:px-10 lg:py-9 xl:grid-cols-[340px_1fr_320px]">
      <div className="h-[620px] animate-pulse rounded-2xl bg-white" />
      <div className="h-[620px] animate-pulse rounded-2xl bg-white" />
      <div className="hidden h-[620px] animate-pulse rounded-2xl bg-white xl:block" />
    </div>
  );
}

function EmptyDocumentsState() {
  return (
    <section className="rounded-2xl border border-dashed border-primary/20 bg-white p-8 text-center shadow-card">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
        <FileText className="h-7 w-7" />
      </div>
      <h2 className="mt-5 font-heading text-2xl font-extrabold">
        Aucun document prêt
      </h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-foreground/60">
        Importez un PDF puis lancez son analyse pour l'utiliser comme base de
        connaissances dans l'assistant pédagogique.
      </p>
      <Link
        className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 font-ui text-sm font-bold text-white shadow-card transition hover:bg-secondary"
        to="/documents"
      >
        <Plus className="h-4 w-4" />
        Préparer un document
      </Link>
    </section>
  );
}

type DocumentPickerProps = {
  documents: DocumentItem[];
  selectedIds: number[];
  onToggle: (documentId: number) => void;
};

function DocumentPicker({
  documents,
  selectedIds,
  onToggle,
}: DocumentPickerProps) {
  return (
    <aside className="rounded-2xl border border-border bg-white p-5 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Corpus
          </p>
          <h2 className="mt-1 font-heading text-xl font-extrabold">
            Documents prêts
          </h2>
        </div>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
          {selectedIds.length}/{documents.length}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {documents.map((document) => {
          const isSelected = selectedIds.includes(document.id);
          return (
            <button
              className={cn(
                "flex w-full items-start gap-3 rounded-xl border p-3 text-left transition",
                isSelected
                  ? "border-primary bg-primary/5 shadow-card"
                  : "border-border bg-white hover:border-primary/30 hover:bg-primary/5",
              )}
              key={document.id}
              onClick={() => onToggle(document.id)}
              type="button"
            >
              <span
                className={cn(
                  "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
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
                <span className="mt-1 block text-xs text-foreground/55">
                  {document.pageCount} pages
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

function WelcomePanel() {
  return (
    <div className="rounded-2xl border border-primary/10 bg-gradient-to-br from-primary/5 via-white to-secondary/5 p-6">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-white shadow-card">
        <Bot className="h-6 w-6" />
      </div>
      <h2 className="mt-5 font-heading text-2xl font-extrabold">
        Assistant pédagogique FormaMind
      </h2>
      <p className="mt-2 max-w-2xl text-sm leading-6 text-foreground/60">
        Posez une question précise sur les documents analysés. L'assistant répond
        uniquement à partir du contenu sélectionné et cite les pages utilisées.
      </p>
    </div>
  );
}

function MessageBubble({ message }: { message: AssistantMessage }) {
  const isUser = message.role === "user";

  return (
    <article className={cn("flex gap-3", isUser && "justify-end")}>
      {!isUser ? (
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-white">
          <Sparkles className="h-4 w-4" />
        </span>
      ) : null}
      <div
        className={cn(
          "max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-7 shadow-card",
          isUser
            ? "bg-primary text-white"
            : "border border-border bg-white text-foreground",
        )}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && message.sources && message.sources.length > 0 ? (
          <div className="mt-4 space-y-2 border-t border-border pt-3">
            {message.sources.map((source) => (
              <div
                className="rounded-lg bg-surface-muted p-3 text-xs text-foreground/65"
                key={`${message.id}-${source.documentId}-${source.pageNumber}`}
              >
                <p className="font-bold text-primary">
                  {source.documentTitle} · page {source.pageNumber}
                </p>
                <p className="mt-1 line-clamp-3">{source.excerpt}</p>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </article>
  );
}

function SourcesPanel({ messages }: { messages: AssistantMessage[] }) {
  const sources = messages.flatMap((message) => message.sources ?? []);

  return (
    <aside className="rounded-2xl border border-border bg-white p-5 shadow-card">
      <div>
        <p className="font-ui text-xs font-extrabold uppercase text-primary">
          Traçabilité
        </p>
        <h2 className="mt-1 font-heading text-xl font-extrabold">
          Sources citées
        </h2>
      </div>

      {sources.length === 0 ? (
        <div className="mt-5 rounded-xl border border-dashed border-border bg-surface-muted/60 p-5 text-sm leading-6 text-foreground/55">
          Les extraits utilisés par l'assistant apparaîtront ici après votre
          première question.
        </div>
      ) : (
        <div className="mt-5 space-y-3">
          {sources.slice(-6).map((source, index) => (
            <article
              className="rounded-xl border border-primary/10 bg-primary/5 p-4"
              key={`${source.documentId}-${source.pageNumber}-${index}`}
            >
              <p className="text-sm font-extrabold text-primary">
                {source.documentTitle}
              </p>
              <p className="mt-1 text-xs font-bold text-foreground/55">
                Page {source.pageNumber}
              </p>
              <p className="mt-3 line-clamp-4 text-xs leading-6 text-foreground/65">
                {source.excerpt}
              </p>
            </article>
          ))}
        </div>
      )}
    </aside>
  );
}

export function AssistantPage() {
  const location = useLocation();
  const locationState = location.state as AssistantLocationState | null;
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<number[]>([]);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
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
  const askMutation = useAskAssistant();
  const readyDocuments = readyDocumentsQuery.data?.items ?? [];

  useEffect(() => {
    const selectedDocumentId = locationState?.selectedDocumentId;
    if (selectedDocumentId && selectedDocumentIds.length === 0) {
      setSelectedDocumentIds([selectedDocumentId]);
    }
  }, [locationState?.selectedDocumentId, selectedDocumentIds.length]);

  function toggleDocument(documentId: number) {
    setFeedback(null);
    setSelectedDocumentIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId],
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    setFeedback(null);

    if (selectedDocumentIds.length === 0) {
      setFeedback("Sélectionnez au moins un document prêt avant de poser une question.");
      return;
    }

    if (!trimmedQuestion) {
      setFeedback("Écrivez une question avant d'envoyer.");
      return;
    }

    const userMessage: AssistantMessage = {
      content: trimmedQuestion,
      id: createMessageId(),
      role: "user",
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");

    askMutation.mutate(
      {
        documentIds: selectedDocumentIds,
        question: trimmedQuestion,
      },
      {
        onError: (error) => {
          setFeedback(getErrorMessage(error));
        },
        onSuccess: (response) => {
          setMessages((current) => [
            ...current,
            {
              content: response.answer,
              id: createMessageId(),
              role: "assistant",
              sources: response.sources,
            },
          ]);
        },
      },
    );
  }

  if (readyDocumentsQuery.isPending) {
    return <AssistantSkeleton />;
  }

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto grid max-w-[1440px] gap-6 lg:grid-cols-[320px_1fr] xl:grid-cols-[340px_1fr_320px]">
        <div className="space-y-6">
          <section>
            <h1 className="font-heading text-4xl font-extrabold tracking-normal text-foreground">
              Assistant IA
            </h1>
            <p className="mt-2 text-sm leading-6 text-foreground/60">
              Interrogez vos supports analysés avec des réponses sourcées.
            </p>
          </section>

          {readyDocumentsQuery.isError ? (
            <div className="rounded-2xl border border-error/20 bg-white p-5 text-sm text-error shadow-card">
              Impossible de charger les documents prêts.
            </div>
          ) : null}

          {readyDocuments.length > 0 ? (
            <DocumentPicker
              documents={readyDocuments}
              onToggle={toggleDocument}
              selectedIds={selectedDocumentIds}
            />
          ) : null}
        </div>

        <section className="flex min-h-[680px] flex-col rounded-2xl border border-border bg-white p-5 shadow-card">
          {readyDocuments.length === 0 ? (
            <div className="flex flex-1 items-center justify-center">
              <EmptyDocumentsState />
            </div>
          ) : (
            <>
              <WelcomePanel />

              <div className="mt-5 flex-1 space-y-5 overflow-y-auto rounded-2xl bg-surface-muted/50 p-4">
                {messages.length === 0 ? (
                  <div className="flex min-h-72 flex-col items-center justify-center text-center">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white text-primary shadow-card">
                      <MessageCircleQuestion className="h-8 w-8" />
                    </div>
                    <h2 className="mt-5 font-heading text-2xl font-extrabold">
                      Commencez avec une question
                    </h2>
                    <p className="mt-2 max-w-md text-sm leading-6 text-foreground/55">
                      Exemple: quels sont les objectifs pédagogiques principaux
                      de ce support ?
                    </p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))
                )}

                {askMutation.isPending ? (
                  <div className="flex items-center gap-3 text-sm font-semibold text-primary">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    L'assistant analyse les documents sélectionnés...
                  </div>
                ) : null}
              </div>

              {feedback ? (
                <div className="mt-4 flex items-start gap-3 rounded-xl border border-error/20 bg-error/5 px-4 py-3 text-sm text-error">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  {feedback}
                </div>
              ) : null}

              <form className="mt-4" onSubmit={handleSubmit}>
                <label className="sr-only" htmlFor="assistant-question">
                  Votre question
                </label>
                <div className="flex gap-3 rounded-2xl border border-border bg-white p-3 focus-within:border-primary">
                  <textarea
                    className="max-h-40 min-h-12 flex-1 resize-none bg-transparent px-2 py-3 text-sm outline-none placeholder:text-foreground/40"
                    disabled={askMutation.isPending}
                    id="assistant-question"
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="Posez une question sur les documents sélectionnés..."
                    value={question}
                  />
                  <button
                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-card transition hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
                    disabled={askMutation.isPending}
                    type="submit"
                  >
                    {askMutation.isPending ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <Send className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </form>
            </>
          )}
        </section>

        <SourcesPanel messages={messages} />
      </div>
    </div>
  );
}
