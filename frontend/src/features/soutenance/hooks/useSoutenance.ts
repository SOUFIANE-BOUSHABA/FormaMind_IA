import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  completeSoutenanceSession,
  createSoutenanceSession,
  deleteSoutenanceSession,
  getCurrentSoutenanceQuestion,
  getSoutenanceResults,
  getSoutenanceSession,
  listSoutenanceSessions,
  submitSoutenanceAnswer,
} from "@/features/soutenance/api/soutenance-api";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { type CreateSoutenanceSessionInput } from "@/features/soutenance/types/soutenance";

export const soutenanceQueryKeys = {
  all: ["soutenance"] as const,
  current: (sessionId: number) => ["soutenance", "current", sessionId] as const,
  detail: (sessionId: number) => ["soutenance", "detail", sessionId] as const,
  list: () => ["soutenance", "list"] as const,
  results: (sessionId: number) => ["soutenance", "results", sessionId] as const,
};

export function useSoutenanceSessions() {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null,
    queryFn: () => listSoutenanceSessions(auth.accessToken ?? ""),
    queryKey: soutenanceQueryKeys.list(),
  });
}

export function useSoutenanceSession(sessionId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && sessionId !== null,
    queryFn: () => getSoutenanceSession(auth.accessToken ?? "", sessionId ?? 0),
    queryKey: soutenanceQueryKeys.detail(sessionId ?? 0),
  });
}

export function useCurrentSoutenanceQuestion(sessionId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && sessionId !== null,
    queryFn: () =>
      getCurrentSoutenanceQuestion(auth.accessToken ?? "", sessionId ?? 0),
    queryKey: soutenanceQueryKeys.current(sessionId ?? 0),
  });
}

export function useSoutenanceResults(sessionId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && sessionId !== null,
    queryFn: () => getSoutenanceResults(auth.accessToken ?? "", sessionId ?? 0),
    queryKey: soutenanceQueryKeys.results(sessionId ?? 0),
  });
}

export function useCreateSoutenanceSession() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateSoutenanceSessionInput) =>
      createSoutenanceSession(auth.accessToken ?? "", input),
    onSuccess: (session) => {
      void queryClient.invalidateQueries({ queryKey: soutenanceQueryKeys.all });
      void queryClient.setQueryData(
        soutenanceQueryKeys.detail(session.id),
        session,
      );
    },
  });
}

export function useSubmitSoutenanceAnswer(sessionId: number) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      answer,
      questionId,
    }: {
      answer: string;
      questionId: number;
    }) =>
      submitSoutenanceAnswer(
        auth.accessToken ?? "",
        sessionId,
        questionId,
        answer,
      ),
    onSuccess: (response) => {
      void queryClient.invalidateQueries({ queryKey: soutenanceQueryKeys.all });
      void queryClient.invalidateQueries({
        queryKey: soutenanceQueryKeys.current(sessionId),
      });
      void queryClient.invalidateQueries({
        queryKey: soutenanceQueryKeys.detail(sessionId),
      });
      if (response.status === "completed") {
        void queryClient.invalidateQueries({
          queryKey: soutenanceQueryKeys.results(sessionId),
        });
      }
    },
  });
}

export function useCompleteSoutenanceSession(sessionId: number) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => completeSoutenanceSession(auth.accessToken ?? "", sessionId),
    onSuccess: (results) => {
      void queryClient.invalidateQueries({ queryKey: soutenanceQueryKeys.all });
      void queryClient.setQueryData(
        soutenanceQueryKeys.results(sessionId),
        results,
      );
    },
  });
}

export function useDeleteSoutenanceSession() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: number) =>
      deleteSoutenanceSession(auth.accessToken ?? "", sessionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: soutenanceQueryKeys.all });
    },
  });
}
