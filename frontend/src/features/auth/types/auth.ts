export type AuthUser = {
  id: number;
  email: string;
  fullName: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
};

export type LoginCredentials = {
  email: string;
  password: string;
};

export type RegisterCredentials = LoginCredentials & {
  fullName: string;
};

export type AuthSession = {
  accessToken: string;
  tokenType: "bearer";
  user: AuthUser;
};
