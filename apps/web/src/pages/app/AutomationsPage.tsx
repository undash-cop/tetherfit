import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Campaign = {
  id: string;
  name: string;
  kind: string;
  active: boolean;
  last_run_at: string | null;
};

export function AutomationsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("Low credit renewal");
  const [kind, setKind] = useState<"renewal" | "birthday" | "announcement">("renewal");
  const [body, setBody] = useState("Hi {{name}}, time to renew your sessions!");

  const campaigns = useQuery({
    queryKey: ["automations"],
    queryFn: () =>
      apiFetch<Campaign[]>("/api/v1/automations/campaigns", { token: getToken() }),
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/automations/campaigns", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          name,
          kind,
          template_subject: name,
          template_body: body,
          channel: "email",
        }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["automations"] }),
  });

  const run = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/automations/campaigns/${id}/run`, {
        method: "POST",
        token: getToken(),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["automations"] }),
  });

  const enablePush = useMutation({
    mutationFn: async () => {
      const key = await apiFetch<{ publicKey: string }>("/api/v1/push/vapid-public-key", {
        token: getToken(),
      });
      // Store a stub subscription when Notification API is unavailable / denied
      const endpoint =
        typeof window !== "undefined"
          ? `https://push.local/stub/${crypto.randomUUID()}`
          : "https://push.local/stub";
      return apiFetch("/api/v1/push/subscribe", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          endpoint,
          p256dh: key.publicKey || "stub-p256dh",
          auth: "stub-auth",
          user_agent: navigator.userAgent,
        }),
      });
    },
  });

  return (
    <section className="space-y-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Automations</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Renewal reminders, birthdays, announcements, and push opt-in.
        </p>
      </div>

      <Button variant="outline" onClick={() => enablePush.mutate()}>
        {enablePush.isSuccess ? "Push subscribed" : "Enable push notifications"}
      </Button>

      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <Label>Name</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
        <Label>Kind</Label>
        <div className="flex gap-2">
          {(["renewal", "birthday", "announcement"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setKind(k)}
              className={`min-h-10 rounded-xl px-3 text-sm font-semibold capitalize ${
                kind === k
                  ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                  : "bg-white/70 dark:bg-white/5"
              }`}
            >
              {k}
            </button>
          ))}
        </div>
        <Label>Message</Label>
        <Input value={body} onChange={(e) => setBody(e.target.value)} />
        <Button onClick={() => create.mutate()}>Create campaign</Button>
      </div>

      <ul className="space-y-2">
        {(campaigns.data ?? []).map((c) => (
          <li
            key={c.id}
            className="flex items-center justify-between gap-2 rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <div>
              <p className="font-semibold">
                {c.name} · {c.kind}
              </p>
              <p className="text-xs text-slate dark:text-sand/60">
                {c.last_run_at
                  ? `Last run ${new Date(c.last_run_at).toLocaleString()}`
                  : "Never run"}
              </p>
            </div>
            <Button variant="secondary" onClick={() => run.mutate(c.id)}>
              Run now
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
