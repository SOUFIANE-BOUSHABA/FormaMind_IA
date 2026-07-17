import { createContext } from "react";

import {
  type AuthUser,
  type LoginCredentials,
  type RegisterCredentials,
} from "@/features/auth/types/auth";

export type AuthStatus = "authenticated" | "unauthenticated";

export type AuthContextValue = {
  accessToken: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (credentials: RegisterCredentials) => Promise<void>;
  reloadUser: () => Promise<void>;
  status: AuthStatus;
  user: AuthUser | null;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
