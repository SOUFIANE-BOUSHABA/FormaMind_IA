import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteLearningPlan,
  generateLearningPlan,
  getLearningPlan,
  listLearningPlans,
  updateLearningActivityStatus,
} from "@/features/learning-plan/api/learning-plan-api";
import {
  type GenerateLearningPlanInput,
  type LearningActivityStatus,
} from "@/features/learning-plan/types/learning-plan";
import { useAuth } from "@/features/auth/hooks/useAuth";

export const learningPlanQueryKeys = {
  all: ["learning-plans"] as const,
  detail: (planId: number) => ["learning-plans", "detail", planId] as const,
  list: () => ["learning-plans", "list"] as const,
};

export function useLearningPlans() {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null,
    queryFn: () => listLearningPlans(auth.accessToken ?? ""),
    queryKey: learningPlanQueryKeys.list(),
  });
}

export function useLearningPlan(planId: number | null) {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null && planId !== null,
    queryFn: () => getLearningPlan(auth.accessToken ?? "", planId ?? 0),
    queryKey: learningPlanQueryKeys.detail(planId ?? 0),
  });
}

export function useGenerateLearningPlan() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: GenerateLearningPlanInput) =>
      generateLearningPlan(auth.accessToken ?? "", input),
    onSuccess: (plan) => {
      void queryClient.invalidateQueries({ queryKey: learningPlanQueryKeys.all });
      void queryClient.setQueryData(learningPlanQueryKeys.detail(plan.id), plan);
    },
  });
}

export function useUpdateLearningActivityStatus(planId: number) {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      activityId,
      status,
    }: {
      activityId: number;
      status: LearningActivityStatus;
    }) =>
      updateLearningActivityStatus(
        auth.accessToken ?? "",
        planId,
        activityId,
        status,
      ),
    onSuccess: (plan) => {
      void queryClient.invalidateQueries({ queryKey: learningPlanQueryKeys.all });
      void queryClient.setQueryData(learningPlanQueryKeys.detail(plan.id), plan);
    },
  });
}

export function useDeleteLearningPlan() {
  const auth = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (planId: number) =>
      deleteLearningPlan(auth.accessToken ?? "", planId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: learningPlanQueryKeys.all });
    },
  });
}
