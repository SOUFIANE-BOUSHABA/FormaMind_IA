import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileText,
  Grid2X2,
  Info,
  List,
  Loader2,
  Search,
  SlidersHorizontal,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { type DragEvent, useMemo, useRef, useState } from "react";

import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  useDeleteDocument,
  useDocument,
  useDocuments,
  useUploadDocument,
} from "@/features/documents/hooks/useDocuments";
import {
  type DocumentItem,
  type DocumentListParams,
  type DocumentSort,
  type DocumentStatus,
  type DocumentViewMode,
} from "@/features/documents/types/documents";

const MAX_UPLOAD_SIZE = 20 * 1024 * 1024;

const statusLabels: Record<DocumentStatus, string> = {
  failed: "Erreur",
  processing: "Traitement en cours",
  ready: "Prêt",
  uploaded: "Importé",
};

const statusClasses: Record<DocumentStatus, string> = {
  failed: "bg-error text-white",
  processing: "bg-accent text-white",
  ready: "bg-secondary text-white",
  uploaded: "bg-primary text-white",
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} Ko`;
  }

  return `${(bytes / 1024 / 1024).toFixed(1)} Mo`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
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

function DocumentsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          className="h-[360px] animate-pulse rounded-xl border border-border bg-white shadow-card"
          key={index}
        >
          <div className="h-44 rounded-t-xl bg-primary/10" />
          <div className="space-y-3 p-4">
            <div className="h-5 w-3/4 rounded bg-primary/10" />
            <div className="h-4 w-1/2 rounded bg-primary/10" />
            <div className="h-20 rounded-lg bg-primary/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

type UploadZoneProps = {
  isUploading: boolean;
  progress: number;
  onFileSelect: (file: File) => void;
};

function UploadZone({ isUploading, progress, onFileSelect }: UploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function handleDrop(event: DragEvent<HTMLButtonElement>) {
    event.preventDefault();
    setIsDragActive(false);
    const file = event.dataTransfer.files.item(0);
    if (file) {
      onFileSelect(file);
    }
  }

  return (
    <section>
      <button
        aria-label="Importer un fichier PDF"
        className={cn(
          "flex w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border-strong bg-white px-5 py-10 text-center transition hover:border-primary hover:bg-primary/5",
          isDragActive && "border-primary bg-primary/5",
        )}
        onClick={() => fileInputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setIsDragActive(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setIsDragActive(false);
        }}
        onDragOver={(event) => {
          event.preventDefault();
        }}
        onDrop={handleDrop}
        type="button"
      >
        <span className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-soft text-primary">
          {isUploading ? (
            <Loader2 className="h-8 w-8 animate-spin" />
          ) : (
            <UploadCloud className="h-8 w-8" />
          )}
        </span>
        <h2 className="mt-5 font-heading text-xl font-bold">
          Glissez-déposez vos fichiers PDF
        </h2>
        <p className="mt-2 max-w-xl text-sm text-foreground/65">
          Ou cliquez pour parcourir votre ordinateur. PDF uniquement — 20 Mo
          maximum.
        </p>

        {isUploading ? (
          <div className="mt-5 w-full max-w-md">
            <div className="h-2 overflow-hidden rounded-full bg-primary/10">
              <div
                className="h-full rounded-full bg-primary transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-2 text-xs font-semibold text-primary">
              Import en cours: {progress}%
            </p>
          </div>
        ) : (
          <div className="mt-5 flex items-center gap-3">
            <span className="rounded-full bg-surface-muted px-3 py-1 text-xs font-bold">
              PDF
            </span>
          </div>
        )}
      </button>

      <input
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={(event) => {
          const file = event.target.files?.item(0);
          if (file) {
            onFileSelect(file);
          }
          event.target.value = "";
        }}
        ref={fileInputRef}
        type="file"
      />
    </section>
  );
}

type DocumentCardProps = {
  document: DocumentItem;
  viewMode: DocumentViewMode;
  onDelete: (document: DocumentItem) => void;
  onOpen: (document: DocumentItem) => void;
};

function DocumentCard({
  document,
  viewMode,
  onDelete,
  onOpen,
}: DocumentCardProps) {
  if (viewMode === "list") {
    return (
      <article className="grid gap-4 rounded-xl border border-border bg-white p-4 shadow-card transition hover:shadow-elevated sm:grid-cols-[88px_1fr_auto] sm:items-center">
        <button
          className="flex h-24 w-full items-center justify-center rounded-lg bg-primary/10 text-primary sm:h-20 sm:w-20"
          onClick={() => onOpen(document)}
          type="button"
        >
          <FileText className="h-9 w-9" />
        </button>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-heading text-lg font-extrabold">
              {document.title}
            </h3>
            <span
              className={cn(
                "rounded px-2 py-1 text-[10px] font-extrabold uppercase",
                statusClasses[document.status],
              )}
            >
              {statusLabels[document.status]}
            </span>
          </div>
          <p className="mt-1 truncate text-sm text-foreground/60">
            {document.originalFilename}
          </p>
          <p className="mt-2 text-xs text-foreground/55">
            {document.pageCount} pages · {formatFileSize(document.fileSize)} ·
            Importé le {formatDate(document.createdAt)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="rounded-lg border border-border px-3 py-2 text-sm font-bold text-primary transition hover:bg-primary/5"
            onClick={() => onOpen(document)}
            type="button"
          >
            Détails
          </button>
          <button
            aria-label={`Supprimer ${document.title}`}
            className="rounded-lg border border-error/20 p-2 text-error transition hover:bg-error/5"
            onClick={() => onDelete(document)}
            type="button"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </article>
    );
  }

  return (
    <article className="flex min-h-[360px] flex-col overflow-hidden rounded-xl border border-border-strong bg-white shadow-card transition hover:shadow-elevated">
      <button
        className="relative flex aspect-[4/3] items-center justify-center overflow-hidden bg-surface-muted text-primary"
        onClick={() => onOpen(document)}
        type="button"
      >
        <span
          className={cn(
            "absolute left-4 top-4 rounded px-2 py-1 text-[10px] font-extrabold uppercase",
            statusClasses[document.status],
          )}
        >
          {statusLabels[document.status]}
        </span>
        <div className="flex h-28 w-24 flex-col items-center justify-center rounded-lg border border-primary/15 bg-white shadow-card">
          <FileText className="h-9 w-9 text-primary" />
          <span className="mt-3 rounded bg-primary/10 px-2 py-1 text-[10px] font-bold text-primary">
            PDF
          </span>
        </div>
      </button>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="truncate font-heading text-lg font-extrabold">
          {document.title}
        </h3>
        <p className="mt-1 truncate text-sm text-foreground/60">
          {document.originalFilename}
        </p>
        <div className="mt-3 flex items-center gap-2 text-xs text-foreground/55">
          <FileText className="h-4 w-4" />
          <span>{document.pageCount} pages</span>
          <span>·</span>
          <span>{formatFileSize(document.fileSize)}</span>
        </div>
        <div className="mt-4 rounded-lg border border-primary/10 bg-white p-3 text-xs text-foreground/65">
          <div className="mb-1 flex items-center gap-2 font-bold text-primary">
            <Info className="h-4 w-4" />
            PDF stocké avec succès
          </div>
          <p>
            Le document est conservé dans votre espace. L'analyse IA sera ajoutée
            dans une prochaine étape.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border bg-surface-muted/50 px-4 py-3">
        <span className="text-[11px] text-foreground/50">
          Importé le {formatDate(document.createdAt)}
        </span>
        <div className="flex items-center gap-1">
          <button
            aria-label={`Voir ${document.title}`}
            className="rounded-lg p-2 text-foreground/60 transition hover:bg-white hover:text-primary"
            onClick={() => onOpen(document)}
            type="button"
          >
            <Info className="h-4 w-4" />
          </button>
          <button
            aria-label={`Supprimer ${document.title}`}
            className="rounded-lg p-2 text-foreground/60 transition hover:bg-error/5 hover:text-error"
            onClick={() => onDelete(document)}
            type="button"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </article>
  );
}

type DetailsPanelProps = {
  documentId: number | null;
  onClose: () => void;
  onDelete: (document: DocumentItem) => void;
};

function DetailsPanel({ documentId, onClose, onDelete }: DetailsPanelProps) {
  const documentQuery = useDocument(documentId);
  const document = documentQuery.data;

  if (documentId === null) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50">
      <button
        aria-label="Fermer les détails"
        className="absolute inset-0 bg-foreground/30"
        onClick={onClose}
        type="button"
      />
      <aside className="absolute bottom-0 right-0 top-0 w-full max-w-md overflow-y-auto bg-white p-6 shadow-elevated">
        <div className="flex items-center justify-between">
          <p className="font-ui text-xs font-extrabold uppercase text-primary">
            Détails du document
          </p>
          <button
            aria-label="Fermer"
            className="rounded-full p-2 text-foreground/60 hover:bg-surface-muted"
            onClick={onClose}
            type="button"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {documentQuery.isLoading ? (
          <div className="mt-8 h-64 animate-pulse rounded-xl bg-primary/10" />
        ) : null}

        {documentQuery.isError ? (
          <div className="mt-8 rounded-xl border border-error/20 bg-error/5 p-4 text-sm text-error">
            Impossible de charger ce document.
          </div>
        ) : null}

        {document ? (
          <div className="mt-8 space-y-6">
            <div className="flex h-48 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <FileText className="h-16 w-16" />
            </div>
            <div>
              <span
                className={cn(
                  "rounded px-2 py-1 text-[10px] font-extrabold uppercase",
                  statusClasses[document.status],
                )}
              >
                {statusLabels[document.status]}
              </span>
              <h2 className="mt-3 font-heading text-2xl font-extrabold">
                {document.title}
              </h2>
              <p className="mt-1 text-sm text-foreground/60">
                {document.originalFilename}
              </p>
            </div>

            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-surface-muted p-3">
                <dt className="text-foreground/50">Pages</dt>
                <dd className="mt-1 font-bold">{document.pageCount}</dd>
              </div>
              <div className="rounded-lg bg-surface-muted p-3">
                <dt className="text-foreground/50">Taille</dt>
                <dd className="mt-1 font-bold">
                  {formatFileSize(document.fileSize)}
                </dd>
              </div>
              <div className="rounded-lg bg-surface-muted p-3">
                <dt className="text-foreground/50">Type</dt>
                <dd className="mt-1 font-bold">PDF</dd>
              </div>
              <div className="rounded-lg bg-surface-muted p-3">
                <dt className="text-foreground/50">Importé</dt>
                <dd className="mt-1 font-bold">{formatDate(document.createdAt)}</dd>
              </div>
            </dl>

            {document.errorMessage ? (
              <div className="rounded-xl border border-error/20 bg-error/5 p-4 text-sm text-error">
                {document.errorMessage}
              </div>
            ) : null}

            <button
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-error/20 px-4 py-3 font-bold text-error transition hover:bg-error/5"
              onClick={() => onDelete(document)}
              type="button"
            >
              <Trash2 className="h-4 w-4" />
              Supprimer le document
            </button>
          </div>
        ) : null}
      </aside>
    </div>
  );
}

type DeleteDialogProps = {
  document: DocumentItem | null;
  isDeleting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

function DeleteDialog({
  document,
  isDeleting,
  onCancel,
  onConfirm,
}: DeleteDialogProps) {
  if (!document) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-foreground/30 px-4">
      <section className="w-full max-w-md rounded-xl border border-border bg-white p-6 shadow-elevated">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error/10 text-error">
          <Trash2 className="h-6 w-6" />
        </div>
        <h2 className="mt-4 font-heading text-xl font-extrabold">
          Supprimer ce document ?
        </h2>
        <p className="mt-2 text-sm text-foreground/65">
          {document.title} sera retiré de votre espace et le fichier local sera
          supprimé.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-lg border border-border px-4 py-2 font-bold text-foreground/70 hover:bg-surface-muted"
            onClick={onCancel}
            type="button"
          >
            Annuler
          </button>
          <button
            className="flex items-center gap-2 rounded-lg bg-error px-4 py-2 font-bold text-white hover:bg-error/90 disabled:opacity-60"
            disabled={isDeleting}
            onClick={onConfirm}
            type="button"
          >
            {isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            Supprimer
          </button>
        </div>
      </section>
    </div>
  );
}

export function DocumentsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<DocumentStatus | "all">("all");
  const [sort, setSort] = useState<DocumentSort>("newest");
  const [page, setPage] = useState(1);
  const [viewMode, setViewMode] = useState<DocumentViewMode>("grid");
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [documentToDelete, setDocumentToDelete] = useState<DocumentItem | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [feedback, setFeedback] = useState<{
    tone: "success" | "error";
    message: string;
  } | null>(null);

  const params = useMemo<DocumentListParams>(
    () => ({
      page,
      pageSize: 12,
      search,
      sort,
      status,
    }),
    [page, search, sort, status],
  );
  const documentsQuery = useDocuments(params);
  const uploadMutation = useUploadDocument();
  const deleteMutation = useDeleteDocument();

  const documents = documentsQuery.data?.items ?? [];
  const total = documentsQuery.data?.total ?? 0;
  const totalPages = documentsQuery.data?.totalPages ?? 0;

  function resetToFirstPage() {
    setPage(1);
  }

  function handleFileSelect(file: File) {
    setFeedback(null);

    if (file.type !== "application/pdf" || !file.name.toLowerCase().endsWith(".pdf")) {
      setFeedback({
        tone: "error",
        message: "Seuls les fichiers PDF sont acceptés.",
      });
      return;
    }

    if (file.size > MAX_UPLOAD_SIZE) {
      setFeedback({
        tone: "error",
        message: "Le fichier PDF dépasse 20 Mo.",
      });
      return;
    }

    setUploadProgress(0);
    uploadMutation.mutate(
      {
        file,
        onProgress: setUploadProgress,
      },
      {
        onError: (error) => {
          setFeedback({ tone: "error", message: getErrorMessage(error) });
        },
        onSuccess: (document) => {
          setFeedback({
            tone: "success",
            message: `${document.title} a été importé avec succès.`,
          });
          setSelectedDocumentId(document.id);
          setUploadProgress(100);
        },
      },
    );
  }

  function handleDeleteConfirm() {
    if (!documentToDelete) {
      return;
    }

    deleteMutation.mutate(documentToDelete.id, {
      onError: (error) => {
        setFeedback({ tone: "error", message: getErrorMessage(error) });
      },
      onSuccess: () => {
        setFeedback({
          tone: "success",
          message: "Document supprimé avec succès.",
        });
        if (selectedDocumentId === documentToDelete.id) {
          setSelectedDocumentId(null);
        }
        setDocumentToDelete(null);
      },
    });
  }

  return (
    <div className="px-4 py-8 pb-28 lg:px-10 lg:py-9">
      <div className="mx-auto max-w-[1440px] space-y-8">
        <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-heading text-4xl font-extrabold tracking-normal text-foreground lg:text-5xl">
              Gestion des Documents
            </h1>
            <p className="mt-2 max-w-2xl text-foreground/65">
              Gérez votre base de connaissances et préparez vos contenus
              pédagogiques.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              className="flex items-center gap-2 rounded-lg border border-border-strong bg-white px-4 py-2.5 font-ui text-sm font-bold text-foreground transition hover:bg-surface-muted"
              type="button"
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filtres
            </button>
            <button
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 font-ui text-sm font-bold text-white shadow-card transition hover:bg-secondary"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              type="button"
            >
              <UploadCloud className="h-4 w-4" />
              Importer
            </button>
          </div>
        </section>

        <UploadZone
          isUploading={uploadMutation.isPending}
          onFileSelect={handleFileSelect}
          progress={uploadProgress}
        />

        {feedback ? (
          <div
            className={cn(
              "flex items-center gap-3 rounded-xl border px-4 py-3 text-sm font-semibold",
              feedback.tone === "success"
                ? "border-success/20 bg-success/5 text-success"
                : "border-error/20 bg-error/5 text-error",
            )}
            role="status"
          >
            {feedback.tone === "success" ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <Info className="h-5 w-5" />
            )}
            {feedback.message}
          </div>
        ) : null}

        <section className="rounded-xl border border-border bg-white p-4 shadow-card">
          <div className="grid gap-4 xl:grid-cols-[1fr_auto_auto_auto] xl:items-center">
            <label className="relative block">
              <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/45" />
              <input
                className="h-11 w-full rounded-lg border border-border bg-surface-muted pl-11 pr-4 text-sm outline-none transition placeholder:text-foreground/40 focus:border-primary"
                onChange={(event) => {
                  setSearch(event.target.value);
                  resetToFirstPage();
                }}
                placeholder="Rechercher un document, un cours..."
                type="search"
                value={search}
              />
            </label>

            <label className="flex items-center gap-2 text-xs font-bold uppercase text-foreground/50">
              Statut:
              <select
                className="h-11 rounded-lg border border-border bg-white px-3 text-sm font-semibold normal-case text-primary outline-none focus:border-primary"
                onChange={(event) => {
                  setStatus(event.target.value as DocumentStatus | "all");
                  resetToFirstPage();
                }}
                value={status}
              >
                <option value="all">Tous les statuts</option>
                <option value="uploaded">Importé</option>
                <option value="processing">Traitement en cours</option>
                <option value="ready">Prêt</option>
                <option value="failed">Erreur</option>
              </select>
            </label>

            <label className="flex items-center gap-2 text-xs font-bold uppercase text-foreground/50">
              Date:
              <select
                className="h-11 rounded-lg border border-border bg-white px-3 text-sm font-semibold normal-case text-primary outline-none focus:border-primary"
                onChange={(event) => {
                  setSort(event.target.value as DocumentSort);
                  resetToFirstPage();
                }}
                value={sort}
              >
                <option value="newest">Plus récents</option>
                <option value="oldest">Plus anciens</option>
                <option value="title_asc">Titre A-Z</option>
                <option value="title_desc">Titre Z-A</option>
              </select>
            </label>

            <div className="flex rounded-lg border border-border bg-surface-muted p-1">
              <button
                aria-label="Affichage en grille"
                className={cn(
                  "rounded-md p-2 transition",
                  viewMode === "grid" ? "bg-white text-primary shadow-card" : "",
                )}
                onClick={() => setViewMode("grid")}
                type="button"
              >
                <Grid2X2 className="h-4 w-4" />
              </button>
              <button
                aria-label="Affichage en liste"
                className={cn(
                  "rounded-md p-2 transition",
                  viewMode === "list" ? "bg-white text-primary shadow-card" : "",
                )}
                onClick={() => setViewMode("list")}
                type="button"
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        {documentsQuery.isLoading ? <DocumentsSkeleton /> : null}

        {documentsQuery.isError ? (
          <section className="rounded-xl border border-error/20 bg-white p-8 text-error shadow-card">
            <h2 className="font-heading text-2xl font-extrabold">
              Impossible de charger les documents
            </h2>
            <p className="mt-2 text-sm">
              Vérifiez que le backend est lancé puis réessayez.
            </p>
          </section>
        ) : null}

        {!documentsQuery.isLoading && !documentsQuery.isError && total === 0 ? (
          <section className="rounded-xl border border-border bg-white p-10 text-center shadow-card">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
              <FileText className="h-8 w-8" />
            </div>
            <h2 className="mt-5 font-heading text-2xl font-extrabold">
              Aucun document pour le moment
            </h2>
            <p className="mx-auto mt-2 max-w-lg text-sm text-foreground/60">
              Importez un premier PDF pour alimenter votre espace documentaire.
              Les fichiers DOCX et PPTX ne sont pas pris en charge dans cette
              étape.
            </p>
          </section>
        ) : null}

        {total > 0 ? (
          <section>
            <div className="mb-4 flex items-center justify-between text-sm text-foreground/55">
              <span>{total} document(s)</span>
              <span>
                Page {page}
                {totalPages > 0 ? ` sur ${totalPages}` : ""}
              </span>
            </div>
            <div
              className={cn(
                viewMode === "grid"
                  ? "grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
                  : "space-y-4",
              )}
            >
              {documents.map((document) => (
                <DocumentCard
                  document={document}
                  key={document.id}
                  onDelete={setDocumentToDelete}
                  onOpen={(selectedDocument) =>
                    setSelectedDocumentId(selectedDocument.id)
                  }
                  viewMode={viewMode}
                />
              ))}
            </div>

            <div className="mt-6 flex items-center justify-end gap-2">
              <button
                aria-label="Page précédente"
                className="rounded-lg border border-border bg-white p-2 text-foreground/65 disabled:opacity-40"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                type="button"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                aria-label="Page suivante"
                className="rounded-lg border border-border bg-white p-2 text-foreground/65 disabled:opacity-40"
                disabled={totalPages === 0 || page >= totalPages}
                onClick={() => setPage((current) => current + 1)}
                type="button"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </section>
        ) : null}
      </div>

      <DetailsPanel
        documentId={selectedDocumentId}
        onClose={() => setSelectedDocumentId(null)}
        onDelete={setDocumentToDelete}
      />
      <DeleteDialog
        document={documentToDelete}
        isDeleting={deleteMutation.isPending}
        onCancel={() => setDocumentToDelete(null)}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
