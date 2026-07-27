import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch, type Dashboard, type PtSession } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<Dashboard>("/api/v1/dashboard", { token: getToken() }),
  });
}

export function useCalendar(from: string, to: string) {
  const params = new URLSearchParams({ from, to });
  return useQuery({
    queryKey: ["calendar", from, to],
    queryFn: () =>
      apiFetch<PtSession[]>(`/api/v1/calendar?${params}`, { token: getToken() }),
    enabled: Boolean(from && to),
  });
}

export function useSession(id: string | undefined) {
  return useQuery({
    queryKey: ["sessions", id],
    queryFn: () => apiFetch<PtSession>(`/api/v1/sessions/${id}`, { token: getToken() }),
    enabled: Boolean(id),
  });
}

export function useCreateSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      client_id: string;
      starts_at: string;
      ends_at: string;
      location?: string;
      notes?: string;
    }) =>
      apiFetch<PtSession>("/api/v1/sessions", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["calendar"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

function useSessionAction(action: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body?: unknown }) =>
      apiFetch<PtSession>(`/api/v1/sessions/${id}/${action}`, {
        method: "POST",
        token: getToken(),
        body: body ? JSON.stringify(body) : undefined,
      }),
    onSuccess: (data) => {
      void qc.invalidateQueries({ queryKey: ["sessions", data.id] });
      void qc.invalidateQueries({ queryKey: ["calendar"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
      void qc.invalidateQueries({ queryKey: ["packages"] });
      void qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

export function useCheckInSession() {
  return useSessionAction("check-in");
}
export function useStartSession() {
  return useSessionAction("start");
}
export function useFinishSession() {
  return useSessionAction("finish");
}
export function useCancelSession() {
  return useSessionAction("cancel");
}

export function useNoShowSession() {
  return useSessionAction("no-show");
}

export function useClientSessions(clientId: string | undefined) {
  const from = new Date();
  from.setFullYear(from.getFullYear() - 1);
  const to = new Date();
  to.setFullYear(to.getFullYear() + 1);
  const params = new URLSearchParams({
    from: from.toISOString(),
    to: to.toISOString(),
  });
  if (clientId) params.set("client_id", clientId);
  return useQuery({
    queryKey: ["sessions", "client", clientId],
    queryFn: () =>
      apiFetch<PtSession[]>(`/api/v1/sessions?${params}`, { token: getToken() }),
    enabled: Boolean(clientId),
  });
}
