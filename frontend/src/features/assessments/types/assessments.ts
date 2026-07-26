export type AssessmentDifficulty =
  | "beginner"
  | "intermediate"
  | "advanced"
  | "adaptive";

export type AssessmentSort = "newest" | "oldest";
export type AssessmentStatus = "generated" | "in_progress" | "completed";

export type QuestionType =
  | "multiple_choice"
  | "true_false"
  | "short_answer"
  | "explanation";

export type GenerateAssessmentInput = {
  documentIds: number[];
  title?: string;
  topics: string[];
  difficulty: AssessmentDifficulty;
  questionCount: number;
  questionTypes: QuestionType[];
};

export type AssessmentDocument = {
  id: number;
  title: string;
  pageCount: number;
};

export type AssessmentQuestionOption = {
  id: number;
  text: string;
  orderIndex: number;
};

export type AssessmentQuestion = {
  id: number;
  type: QuestionType;
  text: string;
  points: number;
  orderIndex: number;
  sourceDocumentId: number;
  sourceDocumentTitle: string;
  sourcePageNumber: number;
  sourceExcerpt: string;
  options: AssessmentQuestionOption[];
};

export type AssessmentSummary = {
  id: number;
  title: string;
  difficulty: AssessmentDifficulty;
  status: AssessmentStatus;
  questionCount: number;
  createdAt: string;
  updatedAt: string;
};

export type AssessmentItem = AssessmentSummary & {
  documents: AssessmentDocument[];
  questions: AssessmentQuestion[];
};

export type AssessmentListParams = {
  page: number;
  pageSize: number;
  sort?: AssessmentSort;
};

export type AssessmentListResponse = {
  items: AssessmentSummary[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};
