export const endpoints = {
  auth: {
    login: "/auth/login",
    me: "/auth/me",
    register: "/auth/register",
  },
  dashboard: {
    summary: "/dashboard/summary",
  },
  documents: {
    detail: (documentId: number) => `/documents/${documentId}`,
    list: "/documents",
    process: (documentId: number) => `/documents/${documentId}/process`,
  },
  assistant: {
    ask: "/assistant/ask",
  },
  assessments: {
    attempts: (assessmentId: number) => `/assessments/${assessmentId}/attempts`,
    detail: (assessmentId: number) => `/assessments/${assessmentId}`,
    list: "/assessments",
  },
  attempts: {
    answer: (attemptId: number, questionId: number) =>
      `/attempts/${attemptId}/answers/${questionId}`,
    detail: (attemptId: number) => `/attempts/${attemptId}`,
    results: (attemptId: number) => `/attempts/${attemptId}/results`,
    submit: (attemptId: number) => `/attempts/${attemptId}/submit`,
  },
  learningPlans: {
    activity: (planId: number, activityId: number) =>
      `/learning-plans/${planId}/activities/${activityId}`,
    detail: (planId: number) => `/learning-plans/${planId}`,
    list: "/learning-plans",
  },
  soutenance: {
    answers: (sessionId: number) => `/soutenance-sessions/${sessionId}/answers`,
    complete: (sessionId: number) =>
      `/soutenance-sessions/${sessionId}/complete`,
    currentQuestion: (sessionId: number) =>
      `/soutenance-sessions/${sessionId}/current-question`,
    detail: (sessionId: number) => `/soutenance-sessions/${sessionId}`,
    list: "/soutenance-sessions",
    results: (sessionId: number) => `/soutenance-sessions/${sessionId}/results`,
  },
  health: "/health",
} as const;
