import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type AssessmentItem,
  type AssessmentListParams,
  type AssessmentListResponse,
  type AssessmentQuestion,
  type AssessmentSummary,
  type GenerateAssessmentInput,
} from "@/features/assessments/types/assessments";
import {
  type AssessmentCoachFeedback,
  type AttemptAnswer,
  type AttemptAnswerInput,
  type AttemptDetail,
  type AttemptHistoryItem,
  type AttemptListResponse,
  type AttemptQuestion,
  type AttemptResults,
  type ResultQuestion,
  type StartAttemptResponse,
} from "@/features/assessments/types/attempts";

type ApiAssessmentDocument = {
  id: number;
  title: string;
  page_count: number;
};

type ApiAssessmentQuestionOption = {
  id: number;
  text: string;
  order_index: number;
};

type ApiAssessmentQuestion = {
  id: number;
  type: AssessmentQuestion["type"];
  text: string;
  points: number;
  order_index: number;
  source_document_id: number;
  source_document_title: string;
  source_page_number: number;
  source_excerpt: string;
  options: ApiAssessmentQuestionOption[];
};

type ApiAssessmentSummary = {
  id: number;
  title: string;
  difficulty: AssessmentSummary["difficulty"];
  status: AssessmentSummary["status"];
  question_count: number;
  created_at: string;
  updated_at: string;
};

type ApiAssessmentRead = ApiAssessmentSummary & {
  documents: ApiAssessmentDocument[];
  questions: ApiAssessmentQuestion[];
};

type ApiAssessmentListResponse = {
  items: ApiAssessmentSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

type ApiAttemptAnswer = {
  question_id: number;
  selected_option_id: number | null;
  text_answer: string | null;
  is_flagged: boolean;
  evaluation_status: AttemptAnswer["evaluationStatus"];
  is_correct: boolean | null;
  points_awarded: number | null;
  feedback: string | null;
  missing_concepts: string[];
};

type ApiAttemptQuestionOption = {
  id: number;
  text: string;
  order_index: number;
};

type ApiAttemptQuestion = {
  id: number;
  type: AttemptQuestion["type"];
  text: string;
  points: number;
  order_index: number;
  options: ApiAttemptQuestionOption[];
};

type ApiAttemptDetail = {
  id: number;
  assessment_id: number;
  assessment_title: string;
  difficulty: AttemptDetail["difficulty"];
  status: AttemptDetail["status"];
  started_at: string;
  submitted_at: string | null;
  evaluated_at: string | null;
  answered_count: number;
  flagged_count: number;
  total_questions: number;
  questions: ApiAttemptQuestion[];
  answers: ApiAttemptAnswer[];
};

type ApiStartAttemptResponse = {
  id: number;
  assessment_id: number;
  status: StartAttemptResponse["status"];
  started_at: string;
  answered_count: number;
  total_questions: number;
};

type ApiAttemptHistoryItem = {
  id: number;
  assessment_id: number;
  status: AttemptHistoryItem["status"];
  score: number | null;
  max_score: number | null;
  percentage: number | null;
  level: string | null;
  started_at: string;
  submitted_at: string | null;
  evaluated_at: string | null;
  answered_count: number;
  total_questions: number;
};

type ApiAttemptListResponse = {
  items: ApiAttemptHistoryItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

type ApiResultQuestionOption = ApiAttemptQuestionOption & {
  is_correct: boolean;
};

type ApiResultQuestion = {
  id: number;
  type: ResultQuestion["type"];
  text: string;
  points: number;
  order_index: number;
  correct_answer: string;
  explanation: string;
  source_document_id: number;
  source_document_title: string;
  source_page_number: number;
  source_excerpt: string;
  options: ApiResultQuestionOption[];
  learner_answer: ApiAttemptAnswer;
};

type ApiAssessmentCoachSource = {
  document_id: number;
  document_title: string;
  page_number: number;
  excerpt: string;
  reason: string;
};

type ApiAssessmentCoachFeedback = {
  score_percent: number;
  mastery_level: AssessmentCoachFeedback["masteryLevel"];
  summary: string;
  points_a_renforcer: string[];
  points_acquis: string[];
  recommended_actions: string[];
  recommended_sources: ApiAssessmentCoachSource[];
  confidence: string;
  refusal_reason: string | null;
};

type ApiAttemptResults = {
  id: number;
  assessment_id: number;
  assessment_title: string;
  difficulty: AttemptResults["difficulty"];
  status: "evaluated";
  score: number;
  max_score: number;
  percentage: number;
  level: string;
  strong_topics: string[];
  weak_topics: string[];
  started_at: string;
  submitted_at: string;
  evaluated_at: string;
  coach_feedback: ApiAssessmentCoachFeedback | null;
  questions: ApiResultQuestion[];
};

function mapSummary(assessment: ApiAssessmentSummary): AssessmentSummary {
  return {
    id: assessment.id,
    title: assessment.title,
    difficulty: assessment.difficulty,
    status: assessment.status,
    questionCount: assessment.question_count,
    createdAt: assessment.created_at,
    updatedAt: assessment.updated_at,
  };
}

function mapAssessment(assessment: ApiAssessmentRead): AssessmentItem {
  return {
    ...mapSummary(assessment),
    documents: assessment.documents.map((document) => ({
      id: document.id,
      title: document.title,
      pageCount: document.page_count,
    })),
    questions: assessment.questions.map((question) => ({
      id: question.id,
      type: question.type,
      text: question.text,
      points: question.points,
      orderIndex: question.order_index,
      sourceDocumentId: question.source_document_id,
      sourceDocumentTitle: question.source_document_title,
      sourcePageNumber: question.source_page_number,
      sourceExcerpt: question.source_excerpt,
      options: question.options.map((option) => ({
        id: option.id,
        text: option.text,
        orderIndex: option.order_index,
      })),
    })),
  };
}

function mapAttemptAnswer(answer: ApiAttemptAnswer): AttemptAnswer {
  return {
    evaluationStatus: answer.evaluation_status,
    feedback: answer.feedback,
    isCorrect: answer.is_correct,
    isFlagged: answer.is_flagged,
    missingConcepts: answer.missing_concepts,
    pointsAwarded: answer.points_awarded,
    questionId: answer.question_id,
    selectedOptionId: answer.selected_option_id,
    textAnswer: answer.text_answer,
  };
}

function mapAttemptQuestion(question: ApiAttemptQuestion): AttemptQuestion {
  return {
    id: question.id,
    options: question.options.map((option) => ({
      id: option.id,
      orderIndex: option.order_index,
      text: option.text,
    })),
    orderIndex: question.order_index,
    points: question.points,
    text: question.text,
    type: question.type,
  };
}

function mapAttemptDetail(attempt: ApiAttemptDetail): AttemptDetail {
  return {
    answers: attempt.answers.map(mapAttemptAnswer),
    answeredCount: attempt.answered_count,
    assessmentId: attempt.assessment_id,
    assessmentTitle: attempt.assessment_title,
    difficulty: attempt.difficulty,
    evaluatedAt: attempt.evaluated_at,
    flaggedCount: attempt.flagged_count,
    id: attempt.id,
    questions: attempt.questions.map(mapAttemptQuestion),
    startedAt: attempt.started_at,
    status: attempt.status,
    submittedAt: attempt.submitted_at,
    totalQuestions: attempt.total_questions,
  };
}

function mapStartAttempt(response: ApiStartAttemptResponse): StartAttemptResponse {
  return {
    answeredCount: response.answered_count,
    assessmentId: response.assessment_id,
    id: response.id,
    startedAt: response.started_at,
    status: response.status,
    totalQuestions: response.total_questions,
  };
}

function mapAttemptHistory(item: ApiAttemptHistoryItem): AttemptHistoryItem {
  return {
    answeredCount: item.answered_count,
    assessmentId: item.assessment_id,
    evaluatedAt: item.evaluated_at,
    id: item.id,
    level: item.level,
    maxScore: item.max_score,
    percentage: item.percentage,
    score: item.score,
    startedAt: item.started_at,
    status: item.status,
    submittedAt: item.submitted_at,
    totalQuestions: item.total_questions,
  };
}

function mapCoachFeedback(
  feedback: ApiAssessmentCoachFeedback | null,
): AssessmentCoachFeedback | null {
  if (feedback === null) {
    return null;
  }

  return {
    confidence: feedback.confidence,
    masteryLevel: feedback.mastery_level,
    pointsAcquis: feedback.points_acquis,
    pointsARenforcer: feedback.points_a_renforcer,
    recommendedActions: feedback.recommended_actions,
    recommendedSources: feedback.recommended_sources.map((source) => ({
      documentId: source.document_id,
      documentTitle: source.document_title,
      excerpt: source.excerpt,
      pageNumber: source.page_number,
      reason: source.reason,
    })),
    refusalReason: feedback.refusal_reason,
    scorePercent: feedback.score_percent,
    summary: feedback.summary,
  };
}

function mapResults(response: ApiAttemptResults): AttemptResults {
  return {
    assessmentId: response.assessment_id,
    assessmentTitle: response.assessment_title,
    coachFeedback: mapCoachFeedback(response.coach_feedback),
    difficulty: response.difficulty,
    evaluatedAt: response.evaluated_at,
    id: response.id,
    level: response.level,
    maxScore: response.max_score,
    percentage: response.percentage,
    questions: response.questions.map((question) => ({
      correctAnswer: question.correct_answer,
      explanation: question.explanation,
      id: question.id,
      learnerAnswer: mapAttemptAnswer(question.learner_answer),
      options: question.options.map((option) => ({
        id: option.id,
        isCorrect: option.is_correct,
        orderIndex: option.order_index,
        text: option.text,
      })),
      orderIndex: question.order_index,
      points: question.points,
      sourceDocumentId: question.source_document_id,
      sourceDocumentTitle: question.source_document_title,
      sourceExcerpt: question.source_excerpt,
      sourcePageNumber: question.source_page_number,
      text: question.text,
      type: question.type,
    })),
    score: response.score,
    startedAt: response.started_at,
    status: response.status,
    strongTopics: response.strong_topics,
    submittedAt: response.submitted_at,
    weakTopics: response.weak_topics,
  };
}

function buildListPath(params: AssessmentListParams): string {
  const searchParams = new URLSearchParams();
  searchParams.set("page", String(params.page));
  searchParams.set("page_size", String(params.pageSize));
  searchParams.set("sort", params.sort ?? "newest");
  return `${endpoints.assessments.list}?${searchParams.toString()}`;
}

export async function listAssessments(
  accessToken: string,
  params: AssessmentListParams,
): Promise<AssessmentListResponse> {
  const response = await apiRequest<ApiAssessmentListResponse>(buildListPath(params), {
    accessToken,
    method: "GET",
  });

  return {
    items: response.items.map(mapSummary),
    page: response.page,
    pageSize: response.page_size,
    total: response.total,
    totalPages: response.total_pages,
  };
}

export async function getAssessment(
  accessToken: string,
  assessmentId: number,
): Promise<AssessmentItem> {
  const response = await apiRequest<ApiAssessmentRead>(
    endpoints.assessments.detail(assessmentId),
    {
      accessToken,
      method: "GET",
    },
  );

  return mapAssessment(response);
}

export async function generateAssessment(
  accessToken: string,
  input: GenerateAssessmentInput,
): Promise<AssessmentItem> {
  const response = await apiRequest<ApiAssessmentRead>(endpoints.assessments.list, {
    accessToken,
    json: {
      difficulty: input.difficulty,
      document_ids: input.documentIds,
      question_count: input.questionCount,
      question_types: input.questionTypes,
      title: input.title,
      topics: input.topics,
    },
    method: "POST",
  });

  return mapAssessment(response);
}

export async function startAssessmentAttempt(
  accessToken: string,
  assessmentId: number,
): Promise<StartAttemptResponse> {
  const response = await apiRequest<ApiStartAttemptResponse>(
    endpoints.assessments.attempts(assessmentId),
    {
      accessToken,
      method: "POST",
    },
  );

  return mapStartAttempt(response);
}

export async function getAttempt(
  accessToken: string,
  attemptId: number,
): Promise<AttemptDetail> {
  const response = await apiRequest<ApiAttemptDetail>(
    endpoints.attempts.detail(attemptId),
    {
      accessToken,
      method: "GET",
    },
  );

  return mapAttemptDetail(response);
}

export async function saveAttemptAnswer(
  accessToken: string,
  attemptId: number,
  questionId: number,
  input: AttemptAnswerInput,
): Promise<AttemptAnswer> {
  const response = await apiRequest<ApiAttemptAnswer>(
    endpoints.attempts.answer(attemptId, questionId),
    {
      accessToken,
      json: {
        is_flagged: input.isFlagged,
        selected_option_id: input.selectedOptionId ?? null,
        text_answer: input.textAnswer ?? null,
      },
      method: "PUT",
    },
  );

  return mapAttemptAnswer(response);
}

export async function submitAttempt(
  accessToken: string,
  attemptId: number,
): Promise<AttemptResults> {
  const response = await apiRequest<ApiAttemptResults>(
    endpoints.attempts.submit(attemptId),
    {
      accessToken,
      method: "POST",
    },
  );

  return mapResults(response);
}

export async function getAttemptResults(
  accessToken: string,
  attemptId: number,
): Promise<AttemptResults> {
  const response = await apiRequest<ApiAttemptResults>(
    endpoints.attempts.results(attemptId),
    {
      accessToken,
      method: "GET",
    },
  );

  return mapResults(response);
}

export async function listAssessmentAttempts(
  accessToken: string,
  assessmentId: number,
): Promise<AttemptListResponse> {
  const response = await apiRequest<ApiAttemptListResponse>(
    endpoints.assessments.attempts(assessmentId),
    {
      accessToken,
      method: "GET",
    },
  );

  return {
    items: response.items.map(mapAttemptHistory),
    page: response.page,
    pageSize: response.page_size,
    total: response.total,
    totalPages: response.total_pages,
  };
}
