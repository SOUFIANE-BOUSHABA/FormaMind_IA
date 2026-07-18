export const endpoints = {
  auth: {
    login: "/auth/login",
    me: "/auth/me",
    register: "/auth/register",
  },
  dashboard: {
    summary: "/dashboard/summary",
  },
  health: "/health",
} as const;
