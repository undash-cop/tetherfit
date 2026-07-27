import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, type Client, type Page, type SessionPackage } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

export function useClients(q = "") {
  const params = new URLSearchParams({ limit: "50", offset: "0" });
  if (q) params.set("q", q);
  return useQuery({
    queryKey: ["clients", q],
    queryFn: () =>
      apiFetch<Page<Client>>(`/api/v1/clients?${params}`, { token: getToken() }),
  });
}

export function useClient(id: string | undefined) {
  return useQuery({
    queryKey: ["clients", id],
    queryFn: () => apiFetch<Client>(`/api/v1/clients/${id}`, { token: getToken() }),
    enabled: Boolean(id),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Client> & { full_name: string }) =>
      apiFetch<Client>("/api/v1/clients", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

export function useUpdateClient(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Client>) =>
      apiFetch<Client>(`/api/v1/clients/${id}`, {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["clients"] });
      void qc.invalidateQueries({ queryKey: ["clients", id] });
    },
  });
}

export function useClientPackages(clientId: string | undefined) {
  return useQuery({
    queryKey: ["packages", clientId],
    queryFn: () =>
      apiFetch<SessionPackage[]>(`/api/v1/clients/${clientId}/packages`, {
        token: getToken(),
      }),
    enabled: Boolean(clientId),
  });
}

export function useCreatePackage(clientId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { total_sessions: number; notes?: string }) =>
      apiFetch<SessionPackage>(`/api/v1/clients/${clientId}/packages`, {
        method: "POST",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["packages", clientId] });
      void qc.invalidateQueries({ queryKey: ["clients", clientId] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
