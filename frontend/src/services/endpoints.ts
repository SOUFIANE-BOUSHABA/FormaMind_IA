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
  health: "/health",
} as const;