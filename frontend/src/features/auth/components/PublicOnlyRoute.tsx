import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/useAuth";

export function PublicOnlyRoute() {
  const auth = useAuth();

  if (auth.status === "authenticated") {
    return <Navigate replace to="/dashboard" />;
  }

  return <Outlet />;
}
