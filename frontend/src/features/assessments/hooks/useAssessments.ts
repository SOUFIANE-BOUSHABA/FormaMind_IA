import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  generateAssessment,
  getAssessment,
  getAttempt,
  getAttemptResults,
  listAssessments,
  listAssessmentAttempts,
  saveAttemptAnswer,
  startAssessmentAttempt,
  submitAttempt,
} from "@/features/assessments/api/assessments-api";
import {
  type AssessmentListParams,
  type GenerateAssessmentInput,
} from "@/features/assessments/types/assessments";
import { type AttemptAnswerInput } from "@/features/assessments/types/attempts";
import { useAuth } from "@/features/auth/hooks/useAuth";

export const assessmentQueryKeys = {
  all: ["assessments"] as const,
  detail: (assessmentId: number) =>
    ["assessments", "detail", assessmentId] as const,
  attempt: (attemptId: number) => ["assessments", "attempt", attemptId] as const,
  attemptResults: (attemptId: number) =>
    ["assessments", "attempt-results", attemptId] as const,
  attempts: (assessmentId: number) =>
    ["assessments", "attempts", assessmentId] as const,
  list: (params: AssessmentListParams) => ["assessments", "list", params] as const,
};

export function useAssessments(params: AssessmentListParams) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null,
    queryFn: () => listAssessments(auth.accessToken ?? "", params),
    queryKey: assessmentQueryKeys.list(params),
  });
}

export function useAssessment(assessmentId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && assessmentId !== null,
    queryFn: () => getAssessment(auth.accessToken ?? "", assessmentId ?? 0),
    queryKey: assessmentQueryKeys.detail(assessmentId ?? 0),
  });
}

export function useGenerateAssessment() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: GenerateAssessmentInput) =>
      generateAssessment(auth.accessToken ?? "", input),
    onSuccess: (assessment) => {
      void queryClient.invalidateQueries({ queryKey: assessmentQueryKeys.all });
      void queryClient.setQueryData(
        assessmentQueryKeys.detail(assessment.id),
        assessment,
      );
    },
  });
}

export function useAssessmentAttempts(assessmentId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && assessmentId !== null,
    queryFn: () =>
      listAssessmentAttempts(auth.accessToken ?? "", assessmentId ?? 0),
    queryKey: assessmentQueryKeys.attempts(assessmentId ?? 0),
  });
}

export function useStartAssessmentAttempt() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (assessmentId: number) =>
      startAssessmentAttempt(auth.accessToken ?? "", assessmentId),
    onSuccess: (attempt) => {
      void queryClient.invalidateQueries({
        queryKey: assessmentQueryKeys.attempts(attempt.assessmentId),
      });
      void queryClient.invalidateQueries({
        queryKey: assessmentQueryKeys.attempt(attempt.id),
      });
    },
  });
}

export function useAttempt(attemptId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && attemptId !== null,
    queryFn: () => getAttempt(auth.accessToken ?? "", attemptId ?? 0),
    queryKey: assessmentQueryKeys.attempt(attemptId ?? 0),
  });
}

export function useSaveAttemptAnswer(attemptId: number) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      input,
      questionId,
    }: {
      input: AttemptAnswerInput;
      questionId: number;
    }) =>
      saveAttemptAnswer(auth.accessToken ?? "", attemptId, questionId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: assessmentQueryKeys.attempt(attemptId),
      });
    },
  });
}

export function useSubmitAttempt(attemptId: number) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => submitAttempt(auth.accessToken ?? "", attemptId),
    onSuccess: (results) => {
      void queryClient.invalidateQueries({ queryKey: assessmentQueryKeys.all });
      void queryClient.setQueryData(
        assessmentQueryKeys.attemptResults(attemptId),
        results,
      );
    },
  });
}

export function useAttemptResults(attemptId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && attemptId !== null,
    queryFn: () => getAttemptResults(auth.accessToken ?? "", attemptId ?? 0),
    queryKey: assessmentQueryKeys.attemptResults(attemptId ?? 0),
  });
}
