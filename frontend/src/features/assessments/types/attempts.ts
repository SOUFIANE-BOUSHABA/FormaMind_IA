import {
  type AssessmentDifficulty,
  type QuestionType,
} from "@/features/assessments/types/assessments";

export type AttemptStatus = "in_progress" | "evaluating" | "evaluated";
export type AnswerEvaluationStatus =
  | "correct"
  | "partial"
  | "incorrect"
  | "unanswered";

export type StartAttemptResponse = {
  id: number;
  assessmentId: number;
  status: AttemptStatus;
  startedAt: string;
  answeredCount: number;
  totalQuestions: number;
};

export type AttemptAnswerInput = {
  selectedOptionId?: number | null;
  textAnswer?: string | null;
  isFlagged: boolean;
};

export type AttemptAnswer = {
  questionId: number;
  selectedOptionId: number | null;
  textAnswer: string | null;
  isFlagged: boolean;
  evaluationStatus: AnswerEvaluationStatus | null;
  isCorrect: boolean | null;
  pointsAwarded: number | null;
  feedback: string | null;
  missingConcepts: string[];
};

export type AttemptQuestionOption = {
  id: number;
  text: string;
  orderIndex: number;
};

export type AttemptQuestion = {
  id: number;
  type: QuestionType;
  text: string;
  points: number;
  orderIndex: number;
  options: AttemptQuestionOption[];
};

export type AttemptDetail = {
  id: number;
  assessmentId: number;
  assessmentTitle: string;
  difficulty: AssessmentDifficulty;
  status: AttemptStatus;
  startedAt: string;
  submittedAt: string | null;
  evaluatedAt: string | null;
  answeredCount: number;
  flaggedCount: number;
  totalQuestions: number;
  questions: AttemptQuestion[];
  answers: AttemptAnswer[];
};

export type AttemptHistoryItem = {
  id: number;
  assessmentId: number;
  status: AttemptStatus;
  score: number | null;
  maxScore: number | null;
  percentage: number | null;
  level: string | null;
  startedAt: string;
  submittedAt: string | null;
  evaluatedAt: string | null;
  answeredCount: number;
  totalQuestions: number;
};

export type AttemptListResponse = {
  items: AttemptHistoryItem[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export type ResultQuestionOption = AttemptQuestionOption & {
  isCorrect: boolean;
};

export type ResultQuestion = {
  id: number;
  type: QuestionType;
  text: string;
  points: number;
  orderIndex: number;
  correctAnswer: string;
  explanation: string;
  sourceDocumentId: number;
  sourceDocumentTitle: string;
  sourcePageNumber: number;
  sourceExcerpt: string;
  options: ResultQuestionOption[];
  learnerAnswer: AttemptAnswer;
};

export type AssessmentCoachSource = {
  documentId: number;
  documentTitle: string;
  pageNumber: number;
  excerpt: string;
  reason: string;
};

export type AssessmentCoachFeedback = {
  scorePercent: number;
  masteryLevel: "weak" | "medium" | "strong";
  summary: string;
  pointsARenforcer: string[];
  pointsAcquis: string[];
  recommendedActions: string[];
  recommendedSources: AssessmentCoachSource[];
  confidence: string;
  refusalReason: string | null;
};

export type AttemptResults = {
  id: number;
  assessmentId: number;
  assessmentTitle: string;
  difficulty: AssessmentDifficulty;
  status: "evaluated";
  score: number;
  maxScore: number;
  percentage: number;
  level: string;
  strongTopics: string[];
  weakTopics: string[];
  startedAt: string;
  submittedAt: string;
  evaluatedAt: string;
  coachFeedback: AssessmentCoachFeedback | null;
  questions: ResultQuestion[];
};
