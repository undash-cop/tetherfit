import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Connection = {
  id: string;
  provider: string;
  display_name: string;
  status: string;
  last_synced_at: string | null;
};

export function IntegrationsPage() {
  const qc = useQueryClient();
  const [provider, setProvider] = useState<"google" | "outlook" | "ics">("ics");
  const [name, setName] = useState("My calendar");

  const connections = useQuery({
    queryKey: ["calendar-connections"],
    queryFn: () =>
      apiFetch<Connection[]>("/api/v1/calendar-connections", { token: getToken() }),
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/calendar-connections", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ provider, display_name: name }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["calendar-connections"] }),
  });

  const sync = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/calendar-connections/${id}/sync`, {
        method: "POST",
        token: getToken(),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["calendar-connections"] }),
  });

  return (
    <section className="space-y-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Integrations</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Connect Google/Outlook calendars or export ICS for any calendar app.
        </p>
      </div>

      <a
        href="/api/v1/calendar/export.ics"
        className="inline-flex min-h-11 items-center justify-center rounded-xl bg-forest px-4 text-sm font-semibold text-sand dark:bg-lime dark:text-ink"
        onClick={(e) => {
          e.preventDefault();
          const token = getToken();
          void fetch("/api/v1/calendar/export.ics", {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          })
            .then((r) => r.blob())
            .then((blob) => {
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "tetherfit-sessions.ics";
              a.click();
              URL.revokeObjectURL(url);
            });
        }}
      >
        Download ICS export
      </a>

      <div className="space-y-3 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <Label>Provider</Label>
        <div className="flex gap-2">
          {(["google", "outlook", "ics"] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setProvider(p)}
              className={`min-h-10 rounded-xl px-3 text-sm font-semibold capitalize ${
                provider === p
                  ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                  : "bg-white/70 dark:bg-white/5"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <Label htmlFor="cal-name">Display name</Label>
        <Input id="cal-name" value={name} onChange={(e) => setName(e.target.value)} />
        <Button disabled={create.isPending} onClick={() => create.mutate()}>
          Connect
        </Button>
      </div>

      <ul className="space-y-2">
        {(connections.data ?? []).map((c) => (
          <li
            key={c.id}
            className="flex items-center justify-between gap-2 rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <div>
              <p className="font-semibold">{c.display_name}</p>
              <p className="text-xs text-slate dark:text-sand/60">
                {c.provider} · {c.status}
                {c.last_synced_at
                  ? ` · synced ${new Date(c.last_synced_at).toLocaleString()}`
                  : ""}
              </p>
            </div>
            <Button variant="outline" onClick={() => sync.mutate(c.id)}>
              Sync
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
