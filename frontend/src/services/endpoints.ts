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
  },
  health: "/health",
} as const;
