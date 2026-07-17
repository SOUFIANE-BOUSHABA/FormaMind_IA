import { type ReactNode, useCallback, useMemo, useState } from "react";

import {
  getMe,
  login as loginRequest,
  register as registerRequest,
} from "@/features/auth/api/auth-api";
import {
  AuthContext,
  type AuthContextValue,
} from "@/features/auth/context/auth-context";
import {
  type AuthUser,
  type LoginCredentials,
  type RegisterCredentials,
} from "@/features/auth/types/auth";

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const session = await loginRequest(credentials);
    setAccessToken(session.accessToken);
    setUser(session.user);
  }, []);

  const register = useCallback(async (credentials: RegisterCredentials) => {
    await registerRequest(credentials);
    const session = await loginRequest({
      email: credentials.email,
      password: credentials.password,
    });
    setAccessToken(session.accessToken);
    setUser(session.user);
  }, []);

  const logout = useCallback(() => {
    setAccessToken(null);
    setUser(null);
  }, []);

  const reloadUser = useCallback(async () => {
    if (accessToken === null) {
      return;
    }

    const currentUser = await getMe(accessToken);
    setUser(currentUser);
  }, [accessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      login,
      logout,
      register,
      reloadUser,
      status: user === null ? "unauthenticated" : "authenticated",
      user,
    }),
    [accessToken, login, logout, register, reloadUser, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
