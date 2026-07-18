import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteDocument,
  getDocument,
  listDocuments,
  uploadDocument,
} from "@/features/documents/api/documents-api";
import {
  type DocumentListParams,
  type UploadDocumentInput,
} from "@/features/documents/types/documents";
import { useAuth } from "@/features/auth/hooks/useAuth";

export const documentQueryKeys = {
  all: ["documents"] as const,
  detail: (documentId: number) => ["documents", "detail", documentId] as const,
  list: (params: DocumentListParams) => ["documents", "list", params] as const,
};

export function useDocuments(params: DocumentListParams) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null,
    queryFn: () => listDocuments(auth.accessToken ?? "", params),
    queryKey: documentQueryKeys.list(params),
  });
}

export function useDocument(documentId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && documentId !== null,
    queryFn: () => getDocument(auth.accessToken ?? "", documentId ?? 0),
    queryKey: documentQueryKeys.detail(documentId ?? 0),
  });
}

export function useUploadDocument() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Omit<UploadDocumentInput, "accessToken">) =>
      uploadDocument({
        ...input,
        accessToken: auth.accessToken ?? "",
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentQueryKeys.all });
      void queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });
}

export function useDeleteDocument() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: number) =>
      deleteDocument(auth.accessToken ?? "", documentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: documentQueryKeys.all });
      void queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });
}
