export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";
export type DocumentSort = "newest" | "oldest" | "title_asc" | "title_desc";
export type DocumentViewMode = "grid" | "list";

export type DocumentItem = {
  id: number;
  title: string;
  originalFilename: string;
  mimeType: string;
  fileSize: number;
  pageCount: number;
  status: DocumentStatus;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
};

export type DocumentListParams = {
  page: number;
  pageSize: number;
  search?: string;
  status?: DocumentStatus | "all";
  sort?: DocumentSort;
};

export type DocumentListResponse = {
  items: DocumentItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export type UploadDocumentInput = {
  accessToken: string;
  file: File;
  title?: string;
  onProgress?: (progress: number) => void;
};
