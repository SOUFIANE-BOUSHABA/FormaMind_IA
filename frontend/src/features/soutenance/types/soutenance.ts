export type SoutenanceMode = "training" | "jury";
export type SoutenanceDifficulty =
  | "beginner"
  | "intermediate"
  | "advanced"
  | "adaptive";
export type SoutenanceStatus = "in_progress" | "completed";
export type SoutenanceAnswerStatus = "waiting" | "answered";
export type SoutenanceCategory =
  | "technical"
  | "architecture"
  | "ai_concepts"
  | "security"
  | "project_choices"
  | "limitations"
  | "testing"
  | "deployment"
  | "jury_challenge";

export type CreateSoutenanceSessionInput = {
  title?: string | null;
  mode: SoutenanceMode;
  difficulty: SoutenanceDifficulty;
  questionCount: number;
  questionCategories: SoutenanceCategory[];
};

export type PublicSoutenanceQuestion = {
  id: number;
  text: string;
  category: SoutenanceCategory;
  categoryLabel: string;
  difficulty: SoutenanceDifficulty;
  orderIndex: number;
  answerStatus: SoutenanceAnswerStatus;
};

export type SoutenanceSession = {
  id: number;
  title: string;
  introduction: string;
  mode: SoutenanceMode;
  difficulty: SoutenanceDifficulty;
  status: SoutenanceStatus;
  questionCount: number;
  answeredCount: number;
  currentQuestionIndex: number;
  progressPercentage: number;
  finalScore: number | null;
  readinessLevel: string | null;
  createdAt: string;
  completedAt: string | null;
  questions: PublicSoutenanceQuestion[];
};

export type SoutenanceSessionListItem = Omit<
  SoutenanceSession,
  "introduction" | "questions"
>;

export type SoutenanceSessionListResponse = {
  items: SoutenanceSessionListItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export type SoutenanceCurrentQuestion = {
  sessionId: number;
  status: SoutenanceStatus;
  mode: SoutenanceMode;
  questionIndex: number;
  totalQuestions: number;
  progressPercentage: number;
  question: PublicSoutenanceQuestion | null;
};

export type SoutenanceRubricCriterion = {
  criterion: string;
  label: string;
  weight: number;
  score: number;
  comment: string;
};

export type SoutenanceAnswerFeedback = {
  totalScore: number;
  feedback: string;
  strengths: string[];
  missingConcepts: string[];
  improvedAnswer: string;
  recommendation: string;
  rubricScores: SoutenanceRubricCriterion[];
};

export type SubmitSoutenanceAnswerResponse = {
  sessionId: number;
  questionId: number;
  mode: SoutenanceMode;
  status: SoutenanceStatus;
  feedback: SoutenanceAnswerFeedback | null;
  nextQuestion: PublicSoutenanceQuestion | null;
  progressPercentage: number;
  message: string;
};

export type SoutenanceQuestionResult = {
  question: PublicSoutenanceQuestion;
  answerText: string;
  feedback: SoutenanceAnswerFeedback;
};

export type SoutenanceCategoryScore = {
  category: SoutenanceCategory;
  categoryLabel: string;
  score: number;
  answeredCount: number;
};

export type SoutenanceResults = {
  id: number;
  title: string;
  mode: SoutenanceMode;
  difficulty: SoutenanceDifficulty;
  finalScore: number;
  readinessLevel: string;
  strengths: string[];
  weaknesses: string[];
  missingConcepts: string[];
  recommendations: string[];
  categoryScores: SoutenanceCategoryScore[];
  questions: SoutenanceQuestionResult[];
  completedAt: string;
};
