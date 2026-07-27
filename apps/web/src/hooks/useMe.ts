import { useQuery } from "@tanstack/react-query";

import { apiFetch, type UserMe } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

export function useMe(enabled = true) {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<UserMe>("/api/v1/me", { token: getToken() }),
    enabled,
    retry: false,
  });
}
