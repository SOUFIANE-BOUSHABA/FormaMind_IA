import { env } from "@/app/config/env";
import { apiRequest, ApiError } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type DocumentItem,
  type DocumentListParams,
  type DocumentListResponse,
  type UploadDocumentInput,
} from "@/features/documents/types/documents";

type ApiDocument = {
  id: number;
  title: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  page_count: number;
  status: DocumentItem["status"];
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

type ApiDocumentListResponse = {
  items: ApiDocument[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

function mapDocument(document: ApiDocument): DocumentItem {
  return {
    id: document.id,
    title: document.title,
    originalFilename: document.original_filename,
    mimeType: document.mime_type,
    fileSize: document.file_size,
    pageCount: document.page_count,
    status: document.status,
    errorMessage: document.error_message,
    createdAt: document.created_at,
    updatedAt: document.updated_at,
  };
}

function mapDocumentList(response: ApiDocumentListResponse): DocumentListResponse {
  return {
    items: response.items.map(mapDocument),
    page: response.page,
    pageSize: response.page_size,
    total: response.total,
    totalPages: response.total_pages,
  };
}

function buildDocumentListPath(params: DocumentListParams): string {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(params.page));
  searchParams.set("page_size", String(params.pageSize));
  searchParams.set("sort", params.sort ?? "newest");

  if (params.search?.trim()) {
    searchParams.set("search", params.search.trim());
  }

  if (params.status && params.status !== "all") {
    searchParams.set("status", params.status);
  }

  return `${endpoints.documents.list}?${searchParams.toString()}`;
}

async function readXhrError(xhr: XMLHttpRequest): Promise<ApiError> {
  let payload: unknown = xhr.responseText;

  if (xhr.responseText) {
    try {
      payload = JSON.parse(xhr.responseText);
    } catch {
      payload = xhr.responseText;
    }
  }

  return new ApiError(xhr.status, payload);
}

export async function listDocuments(
  accessToken: string,
  params: DocumentListParams,
): Promise<DocumentListResponse> {
  const response = await apiRequest<ApiDocumentListResponse>(
    buildDocumentListPath(params),
    {
      accessToken,
      method: "GET",
    },
  );

  return mapDocumentList(response);
}

export async function getDocument(
  accessToken: string,
  documentId: number,
): Promise<DocumentItem> {
  const response = await apiRequest<ApiDocument>(
    endpoints.documents.detail(documentId),
    {
      accessToken,
      method: "GET",
    },
  );

  return mapDocument(response);
}

export async function deleteDocument(
  accessToken: string,
  documentId: number,
): Promise<void> {
  await apiRequest<void>(endpoints.documents.detail(documentId), {
    accessToken,
    method: "DELETE",
  });
}

export async function uploadDocument({
  accessToken,
  file,
  title,
  onProgress,
}: UploadDocumentInput): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  if (title?.trim()) {
    formData.append("title", title.trim());
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${env.VITE_API_BASE_URL}${endpoints.documents.list}`);
    xhr.setRequestHeader("Authorization", `Bearer ${accessToken}`);
    xhr.withCredentials = true;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const payload = JSON.parse(xhr.responseText) as ApiDocument;
        resolve(mapDocument(payload));
        return;
      }

      void readXhrError(xhr).then(reject).catch(reject);
    };

    xhr.onerror = () => {
      reject(new Error("L'import du document a échoué."));
    };

    xhr.send(formData);
  });
}
