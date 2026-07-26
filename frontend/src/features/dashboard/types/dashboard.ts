export type DashboardTone =
  | "primary"
  | "secondary"
  | "accent"
  | "success"
  | "warning"
  | "error";

export type DashboardMetric = {
  label: string;
  value: string;
  description: string;
  icon: string;
  tone: DashboardTone;
  trend: string | null;
  progress: number | null;
};

export type SkillMetric = {
  label: string;
  value: number;
  highlighted: boolean;
};

export type AgentStatus = "online" | "active" | "waiting";

export type AgentActivity = {
  name: string;
  status: AgentStatus;
  description: string;
  tone: "primary" | "secondary" | "accent";
};

export type Recommendation = {
  eyebrow: string;
  title: string;
  duration: string;
  badge: string;
  description: string;
  actionLabel: string;
  planId: number | null;
  activityId: number | null;
  scheduledDate: string | null;
};

export type FocusArea = {
  label: string;
  severity: "critical" | "important";
  progress: number;
};

export type ActivityEntry = {
  title: string;
  description: string;
  timestamp: string;
  tone: "primary" | "secondary" | "accent";
};

export type DashboardSummary = {
  learnerName: string;
  learnerTitle: string;
  greeting: string;
  subtitle: string;
  metrics: DashboardMetric[];
  skills: SkillMetric[];
  agents: AgentActivity[];
  recommendation: Recommendation | null;
  focusAreas: FocusArea[];
  recentActivity: ActivityEntry[];
};
