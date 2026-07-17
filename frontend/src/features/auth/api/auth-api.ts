import { apiRequest } from "@/lib/api-client";
import { endpoints } from "@/services/endpoints";
import {
  type AuthSession,
  type AuthUser,
  type LoginCredentials,
  type RegisterCredentials,
} from "@/features/auth/types/auth";

type ApiUser = {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: ApiUser;
};

function mapUser(user: ApiUser): AuthUser {
  return {
    id: user.id,
    email: user.email,
    fullName: user.full_name,
    isActive: user.is_active,
    createdAt: user.created_at,
    updatedAt: user.updated_at,
  };
}

function mapSession(session: TokenResponse): AuthSession {
  return {
    accessToken: session.access_token,
    tokenType: session.token_type,
    user: mapUser(session.user),
  };
}

export async function login(credentials: LoginCredentials): Promise<AuthSession> {
  const session = await apiRequest<TokenResponse>(endpoints.auth.login, {
    json: credentials,
    method: "POST",
  });

  return mapSession(session);
}

export async function register(
  credentials: RegisterCredentials,
): Promise<AuthUser> {
  const user = await apiRequest<ApiUser>(endpoints.auth.register, {
    json: {
      email: credentials.email,
      full_name: credentials.fullName,
      password: credentials.password,
    },
    method: "POST",
  });

  return mapUser(user);
}

export async function getMe(accessToken: string): Promise<AuthUser> {
  const user = await apiRequest<ApiUser>(endpoints.auth.me, {
    accessToken,
    method: "GET",
  });

  return mapUser(user);
}
