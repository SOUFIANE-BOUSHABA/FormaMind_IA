import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type ActivityEntry,
  type AgentActivity,
  type DashboardMetric,
  type DashboardSummary,
  type FocusArea,
  type Recommendation,
  type SkillMetric,
} from "@/features/dashboard/types/dashboard";

type ApiDashboardMetric = {
  label: string;
  value: string;
  description: string;
  icon: string;
  tone: DashboardMetric["tone"];
  trend: string | null;
  progress: number | null;
};

type ApiSkillMetric = SkillMetric;
type ApiAgentActivity = AgentActivity;

type ApiRecommendation = {
  eyebrow: string;
  title: string;
  duration: string;
  badge: string;
  description: string;
  action_label: string;
};

type ApiFocusArea = FocusArea;
type ApiActivityEntry = ActivityEntry;

type ApiDashboardSummary = {
  learner_name: string;
  learner_title: string;
  greeting: string;
  subtitle: string;
  metrics: ApiDashboardMetric[];
  skills: ApiSkillMetric[];
  agents: ApiAgentActivity[];
  recommendation: ApiRecommendation | null;
  focus_areas: ApiFocusArea[];
  recent_activity: ApiActivityEntry[];
};

function mapRecommendation(
  recommendation: ApiRecommendation | null,
): Recommendation | null {
  if (recommendation === null) {
    return null;
  }

  return {
    eyebrow: recommendation.eyebrow,
    title: recommendation.title,
    duration: recommendation.duration,
    badge: recommendation.badge,
    description: recommendation.description,
    actionLabel: recommendation.action_label,
  };
}

function mapSummary(summary: ApiDashboardSummary): DashboardSummary {
  return {
    learnerName: summary.learner_name,
    learnerTitle: summary.learner_title,
    greeting: summary.greeting,
    subtitle: summary.subtitle,
    metrics: summary.metrics,
    skills: summary.skills,
    agents: summary.agents,
    recommendation: mapRecommendation(summary.recommendation),
    focusAreas: summary.focus_areas,
    recentActivity: summary.recent_activity,
  };
}

export async function getDashboardSummary(
  accessToken: string,
): Promise<DashboardSummary> {
  const summary = await apiRequest<ApiDashboardSummary>(endpoints.dashboard.summary, {
    accessToken,
    method: "GET",
  });

  return mapSummary(summary);
}
