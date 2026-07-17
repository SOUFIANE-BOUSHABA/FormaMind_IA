export const endpoints = {
  auth: {
    login: "/auth/login",
    me: "/auth/me",
    register: "/auth/register",
  },
  health: "/health",
} as const;
