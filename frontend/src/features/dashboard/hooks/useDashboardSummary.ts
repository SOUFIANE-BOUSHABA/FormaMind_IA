import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/features/auth/hooks/useAuth";
import { getDashboardSummary } from "@/features/dashboard/api/dashboard-api";

export function useDashboardSummary() {
  const auth = useAuth();

  return useQuery({
    enabled: auth.accessToken !== null,
    queryFn: () => getDashboardSummary(auth.accessToken ?? ""),
    queryKey: ["dashboard", "summary"],
  });
}
