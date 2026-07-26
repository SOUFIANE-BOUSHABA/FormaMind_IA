import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type GenerateLearningPlanInput,
  type LearningActivity,
  type LearningActivityStatus,
  type LearningModule,
  type LearningPlan,
  type LearningPlanListItem,
  type LearningPlanListResponse,
  type LearningPlanSource,
} from "@/features/learning-plan/types/learning-plan";

type ApiLearningPlanSource = {
  document_id: number;
  document_title: string;
  page_number: number;
  excerpt: string;
};

type ApiLearningActivity = {
  id: number;
  title: string;
  instructions: string;
  type: LearningActivity["type"];
  status: LearningActivity["status"];
  order_index: number;
  scheduled_date: string;
  duration_minutes: number;
  started_at: string | null;
  completed_at: string | null;
  sources: ApiLearningPlanSource[];
};

type ApiLearningModule = {
  id: number;
  title: string;
  objective: string;
  topic: string;
  priority: LearningModule["priority"];
  order_index: number;
  estimated_minutes: number;
  activities: ApiLearningActivity[];
};

type ApiLearningPlan = {
  id: number;
  attempt_id: number;
  assessment_title: string;
  title: string;
  status: LearningPlan["status"];
  intensity: LearningPlan["intensity"];
  daily_minutes: number;
  start_date: string;
  target_end_date: string;
  progress_percentage: number;
  generated_summary: string;
  created_at: string;
  updated_at: string;
  modules: ApiLearningModule[];
};

type ApiLearningPlanListItem = {
  id: number;
  attempt_id: number;
  assessment_title: string;
  title: string;
  status: LearningPlanListItem["status"];
  intensity: LearningPlanListItem["intensity"];
  daily_minutes: number;
  start_date: string;
  target_end_date: string;
  progress_percentage: number;
  next_activity_title: string | null;
  next_activity_date: string | null;
  created_at: string;
};

type ApiLearningPlanListResponse = {
  items: ApiLearningPlanListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

function mapSource(source: ApiLearningPlanSource): LearningPlanSource {
  return {
    documentId: source.document_id,
    documentTitle: source.document_title,
    excerpt: source.excerpt,
    pageNumber: source.page_number,
  };
}

function mapActivity(activity: ApiLearningActivity): LearningActivity {
  return {
    completedAt: activity.completed_at,
    durationMinutes: activity.duration_minutes,
    id: activity.id,
    instructions: activity.instructions,
    orderIndex: activity.order_index,
    scheduledDate: activity.scheduled_date,
    sources: activity.sources.map(mapSource),
    startedAt: activity.started_at,
    status: activity.status,
    title: activity.title,
    type: activity.type,
  };
}

function mapModule(module: ApiLearningModule): LearningModule {
  return {
    activities: module.activities.map(mapActivity),
    estimatedMinutes: module.estimated_minutes,
    id: module.id,
    objective: module.objective,
    orderIndex: module.order_index,
    priority: module.priority,
    title: module.title,
    topic: module.topic,
  };
}

function mapPlan(plan: ApiLearningPlan): LearningPlan {
  return {
    assessmentTitle: plan.assessment_title,
    attemptId: plan.attempt_id,
    createdAt: plan.created_at,
    dailyMinutes: plan.daily_minutes,
    generatedSummary: plan.generated_summary,
    id: plan.id,
    intensity: plan.intensity,
    modules: plan.modules.map(mapModule),
    progressPercentage: plan.progress_percentage,
    startDate: plan.start_date,
    status: plan.status,
    targetEndDate: plan.target_end_date,
    title: plan.title,
    updatedAt: plan.updated_at,
  };
}

function mapListItem(item: ApiLearningPlanListItem): LearningPlanListItem {
  return {
    assessmentTitle: item.assessment_title,
    attemptId: item.attempt_id,
    createdAt: item.created_at,
    dailyMinutes: item.daily_minutes,
    id: item.id,
    intensity: item.intensity,
    nextActivityDate: item.next_activity_date,
    nextActivityTitle: item.next_activity_title,
    progressPercentage: item.progress_percentage,
    startDate: item.start_date,
    status: item.status,
    targetEndDate: item.target_end_date,
    title: item.title,
  };
}

export async function listLearningPlans(
  accessToken: string,
): Promise<LearningPlanListResponse> {
  const response = await apiRequest<ApiLearningPlanListResponse>(
    endpoints.learningPlans.list,
    {
      accessToken,
      method: "GET",
    },
  );

  return {
    items: response.items.map(mapListItem),
    page: response.page,
    pageSize: response.page_size,
    total: response.total,
    totalPages: response.total_pages,
  };
}

export async function getLearningPlan(
  accessToken: string,
  planId: number,
): Promise<LearningPlan> {
  const response = await apiRequest<ApiLearningPlan>(
    endpoints.learningPlans.detail(planId),
    {
      accessToken,
      method: "GET",
    },
  );
  return mapPlan(response);
}

export async function generateLearningPlan(
  accessToken: string,
  input: GenerateLearningPlanInput,
): Promise<LearningPlan> {
  const response = await apiRequest<ApiLearningPlan>(
    endpoints.learningPlans.list,
    {
      accessToken,
      json: {
        attempt_id: input.attemptId,
        daily_minutes: input.dailyMinutes,
        intensity: input.intensity,
        start_date: input.startDate,
        title: input.title ?? null,
      },
      method: "POST",
    },
  );
  return mapPlan(response);
}

export async function updateLearningActivityStatus(
  accessToken: string,
  planId: number,
  activityId: number,
  status: LearningActivityStatus,
): Promise<LearningPlan> {
  const response = await apiRequest<ApiLearningPlan>(
    endpoints.learningPlans.activity(planId, activityId),
    {
      accessToken,
      json: { status },
      method: "PATCH",
    },
  );
  return mapPlan(response);
}

export async function deleteLearningPlan(
  accessToken: string,
  planId: number,
): Promise<void> {
  await apiRequest<void>(endpoints.learningPlans.detail(planId), {
    accessToken,
    method: "DELETE",
  });
}
