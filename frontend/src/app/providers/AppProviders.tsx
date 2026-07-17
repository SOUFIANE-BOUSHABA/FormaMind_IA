import { type ReactNode } from "react";

import { QueryProvider } from "@/app/providers/QueryProvider";
import { AuthProvider } from "@/features/auth/context/AuthContext";

type AppProvidersProps = {
  children: ReactNode;
};

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryProvider>
      <AuthProvider>{children}</AuthProvider>
    </QueryProvider>
  );
}
