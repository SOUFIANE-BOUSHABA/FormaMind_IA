export type LearningPlanStatus = "active" | "completed";
export type LearningPlanIntensity = "light" | "balanced" | "intensive";
export type LearningActivityStatus = "pending" | "in_progress" | "completed";
export type LearningActivityType = "review" | "practice" | "quiz" | "reflection";
export type LearningModulePriority = "high" | "medium" | "low";

export type GenerateLearningPlanInput = {
  attemptId: number;
  title?: string | null;
  dailyMinutes: number;
  startDate: string;
  intensity: LearningPlanIntensity;
};

export type LearningPlanSource = {
  documentId: number;
  documentTitle: string;
  pageNumber: number;
  excerpt: string;
};

export type LearningActivity = {
  id: number;
  title: string;
  instructions: string;
  type: LearningActivityType;
  status: LearningActivityStatus;
  orderIndex: number;
  scheduledDate: string;
  durationMinutes: number;
  startedAt: string | null;
  completedAt: string | null;
  sources: LearningPlanSource[];
};

export type LearningModule = {
  id: number;
  title: string;
  objective: string;
  topic: string;
  priority: LearningModulePriority;
  orderIndex: number;
  estimatedMinutes: number;
  activities: LearningActivity[];
};

export type LearningPlan = {
  id: number;
  attemptId: number;
  assessmentTitle: string;
  title: string;
  status: LearningPlanStatus;
  intensity: LearningPlanIntensity;
  dailyMinutes: number;
  startDate: string;
  targetEndDate: string;
  progressPercentage: number;
  generatedSummary: string;
  createdAt: string;
  updatedAt: string;
  modules: LearningModule[];
};

export type LearningPlanListItem = {
  id: number;
  attemptId: number;
  assessmentTitle: string;
  title: string;
  status: LearningPlanStatus;
  intensity: LearningPlanIntensity;
  dailyMinutes: number;
  startDate: string;
  targetEndDate: string;
  progressPercentage: number;
  nextActivityTitle: string | null;
  nextActivityDate: string | null;
  createdAt: string;
};

export type LearningPlanListResponse = {
  items: LearningPlanListItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};
