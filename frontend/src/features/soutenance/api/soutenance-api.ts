import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type CreateSoutenanceSessionInput,
  type PublicSoutenanceQuestion,
  type SoutenanceAnswerFeedback,
  type SoutenanceCategoryScore,
  type SoutenanceCurrentQuestion,
  type SoutenanceResults,
  type SoutenanceSession,
  type SoutenanceSessionListItem,
  type SoutenanceSessionListResponse,
  type SubmitSoutenanceAnswerResponse,
} from "@/features/soutenance/types/soutenance";

type ApiPublicSoutenanceQuestion = {
  id: number;
  text: string;
  category: PublicSoutenanceQuestion["category"];
  category_label: string;
  difficulty: PublicSoutenanceQuestion["difficulty"];
  order_index: number;
  answer_status: PublicSoutenanceQuestion["answerStatus"];
};

type ApiSoutenanceSession = {
  id: number;
  title: string;
  introduction: string;
  mode: SoutenanceSession["mode"];
  difficulty: SoutenanceSession["difficulty"];
  status: SoutenanceSession["status"];
  question_count: number;
  answered_count: number;
  current_question_index: number;
  progress_percentage: number;
  final_score: number | null;
  readiness_level: string | null;
  created_at: string;
  completed_at: string | null;
  questions: ApiPublicSoutenanceQuestion[];
};

type ApiSoutenanceListItem = Omit<
  ApiSoutenanceSession,
  "introduction" | "questions"
>;

type ApiSoutenanceListResponse = {
  items: ApiSoutenanceListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

type ApiSoutenanceCurrentQuestion = {
  session_id: number;
  status: SoutenanceCurrentQuestion["status"];
  mode: SoutenanceCurrentQuestion["mode"];
  question_index: number;
  total_questions: number;
  progress_percentage: number;
  question: ApiPublicSoutenanceQuestion | null;
};

type ApiSoutenanceRubricCriterion = {
  criterion: string;
  label: string;
  weight: number;
  score: number;
  comment: string;
};

type ApiSoutenanceAnswerFeedback = {
  total_score: number;
  feedback: string;
  strengths: string[];
  missing_concepts: string[];
  improved_answer: string;
  recommendation: string;
  rubric_scores: ApiSoutenanceRubricCriterion[];
};

type ApiSubmitSoutenanceAnswerResponse = {
  session_id: number;
  question_id: number;
  mode: SubmitSoutenanceAnswerResponse["mode"];
  status: SubmitSoutenanceAnswerResponse["status"];
  feedback: ApiSoutenanceAnswerFeedback | null;
  next_question: ApiPublicSoutenanceQuestion | null;
  progress_percentage: number;
  message: string;
};

type ApiSoutenanceCategoryScore = {
  category: SoutenanceCategoryScore["category"];
  category_label: string;
  score: number;
  answered_count: number;
};

type ApiSoutenanceQuestionResult = {
  question: ApiPublicSoutenanceQuestion;
  answer_text: string;
  feedback: ApiSoutenanceAnswerFeedback;
};

type ApiSoutenanceResults = {
  id: number;
  title: string;
  mode: SoutenanceResults["mode"];
  difficulty: SoutenanceResults["difficulty"];
  final_score: number;
  readiness_level: string;
  strengths: string[];
  weaknesses: string[];
  missing_concepts: string[];
  recommendations: string[];
  category_scores: ApiSoutenanceCategoryScore[];
  questions: ApiSoutenanceQuestionResult[];
  completed_at: string;
};

function mapQuestion(
  question: ApiPublicSoutenanceQuestion,
): PublicSoutenanceQuestion {
  return {
    answerStatus: question.answer_status,
    category: question.category,
    categoryLabel: question.category_label,
    difficulty: question.difficulty,
    id: question.id,
    orderIndex: question.order_index,
    text: question.text,
  };
}

function mapSession(session: ApiSoutenanceSession): SoutenanceSession {
  return {
    answeredCount: session.answered_count,
    completedAt: session.completed_at,
    createdAt: session.created_at,
    currentQuestionIndex: session.current_question_index,
    difficulty: session.difficulty,
    finalScore: session.final_score,
    id: session.id,
    introduction: session.introduction,
    mode: session.mode,
    progressPercentage: session.progress_percentage,
    questionCount: session.question_count,
    questions: session.questions.map(mapQuestion),
    readinessLevel: session.readiness_level,
    status: session.status,
    title: session.title,
  };
}

function mapListItem(
  item: ApiSoutenanceListItem,
): SoutenanceSessionListItem {
  return {
    answeredCount: item.answered_count,
    completedAt: item.completed_at,
    createdAt: item.created_at,
    currentQuestionIndex: item.current_question_index,
    difficulty: item.difficulty,
    finalScore: item.final_score,
    id: item.id,
    mode: item.mode,
    progressPercentage: item.progress_percentage,
    questionCount: item.question_count,
    readinessLevel: item.readiness_level,
    status: item.status,
    title: item.title,
  };
}

function mapFeedback(
  feedback: ApiSoutenanceAnswerFeedback,
): SoutenanceAnswerFeedback {
  return {
    feedback: feedback.feedback,
    improvedAnswer: feedback.improved_answer,
    missingConcepts: feedback.missing_concepts,
    recommendation: feedback.recommendation,
    rubricScores: feedback.rubric_scores.map((score) => ({
      comment: score.comment,
      criterion: score.criterion,
      label: score.label,
      score: score.score,
      weight: score.weight,
    })),
    strengths: feedback.strengths,
    totalScore: feedback.total_score,
  };
}

function mapCurrentQuestion(
  response: ApiSoutenanceCurrentQuestion,
): SoutenanceCurrentQuestion {
  return {
    mode: response.mode,
    progressPercentage: response.progress_percentage,
    question: response.question ? mapQuestion(response.question) : null,
    questionIndex: response.question_index,
    sessionId: response.session_id,
    status: response.status,
    totalQuestions: response.total_questions,
  };
}

function mapSubmitResponse(
  response: ApiSubmitSoutenanceAnswerResponse,
): SubmitSoutenanceAnswerResponse {
  return {
    feedback: response.feedback ? mapFeedback(response.feedback) : null,
    message: response.message,
    mode: response.mode,
    nextQuestion: response.next_question
      ? mapQuestion(response.next_question)
      : null,
    progressPercentage: response.progress_percentage,
    questionId: response.question_id,
    sessionId: response.session_id,
    status: response.status,
  };
}

function mapResults(response: ApiSoutenanceResults): SoutenanceResults {
  return {
    categoryScores: response.category_scores.map((score) => ({
      answeredCount: score.answered_count,
      category: score.category,
      categoryLabel: score.category_label,
      score: score.score,
    })),
    completedAt: response.completed_at,
    difficulty: response.difficulty,
    finalScore: response.final_score,
    id: response.id,
    missingConcepts: response.missing_concepts,
    mode: response.mode,
    questions: response.questions.map((item) => ({
      answerText: item.answer_text,
      feedback: mapFeedback(item.feedback),
      question: mapQuestion(item.question),
    })),
    readinessLevel: response.readiness_level,
    recommendations: response.recommendations,
    strengths: response.strengths,
    title: response.title,
    weaknesses: response.weaknesses,
  };
}

export async function listSoutenanceSessions(
  accessToken: string,
): Promise<SoutenanceSessionListResponse> {
  const response = await apiRequest<ApiSoutenanceListResponse>(
    endpoints.soutenance.list,
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

export async function createSoutenanceSession(
  accessToken: string,
  input: CreateSoutenanceSessionInput,
): Promise<SoutenanceSession> {
  const response = await apiRequest<ApiSoutenanceSession>(
    endpoints.soutenance.list,
    {
      accessToken,
      json: {
        difficulty: input.difficulty,
        mode: input.mode,
        question_categories: input.questionCategories,
        question_count: input.questionCount,
        title: input.title ?? null,
      },
      method: "POST",
    },
  );
  return mapSession(response);
}

export async function getSoutenanceSession(
  accessToken: string,
  sessionId: number,
): Promise<SoutenanceSession> {
  const response = await apiRequest<ApiSoutenanceSession>(
    endpoints.soutenance.detail(sessionId),
    {
      accessToken,
      method: "GET",
    },
  );
  return mapSession(response);
}

export async function getCurrentSoutenanceQuestion(
  accessToken: string,
  sessionId: number,
): Promise<SoutenanceCurrentQuestion> {
  const response = await apiRequest<ApiSoutenanceCurrentQuestion>(
    endpoints.soutenance.currentQuestion(sessionId),
    {
      accessToken,
      method: "GET",
    },
  );
  return mapCurrentQuestion(response);
}

export async function submitSoutenanceAnswer(
  accessToken: string,
  sessionId: number,
  questionId: number,
  answer: string,
): Promise<SubmitSoutenanceAnswerResponse> {
  const response = await apiRequest<ApiSubmitSoutenanceAnswerResponse>(
    endpoints.soutenance.answers(sessionId),
    {
      accessToken,
      json: {
        answer,
        question_id: questionId,
      },
      method: "POST",
    },
  );
  return mapSubmitResponse(response);
}

export async function completeSoutenanceSession(
  accessToken: string,
  sessionId: number,
): Promise<SoutenanceResults> {
  const response = await apiRequest<ApiSoutenanceResults>(
    endpoints.soutenance.complete(sessionId),
    {
      accessToken,
      method: "POST",
    },
  );
  return mapResults(response);
}

export async function getSoutenanceResults(
  accessToken: string,
  sessionId: number,
): Promise<SoutenanceResults> {
  const response = await apiRequest<ApiSoutenanceResults>(
    endpoints.soutenance.results(sessionId),
    {
      accessToken,
      method: "GET",
    },
  );
  return mapResults(response);
}

export async function deleteSoutenanceSession(
  accessToken: string,
  sessionId: number,
): Promise<void> {
  await apiRequest<void>(endpoints.soutenance.detail(sessionId), {
    accessToken,
    method: "DELETE",
  });
}
