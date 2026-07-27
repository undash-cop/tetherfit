import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Session = { id: string; starts_at: string; status: string; location: string | null };

export function ClientBookPage() {
  const qc = useQueryClient();
  const [starts, setStarts] = useState("");
  const sessions = useQuery({
    queryKey: ["portal-sessions"],
    queryFn: () => apiFetch<Session[]>("/api/v1/portal/sessions", { token: getToken() }),
  });
  const home = useQuery({
    queryKey: ["portal-home"],
    queryFn: () =>
      apiFetch<{ client_id: string }>("/api/v1/portal/home", { token: getToken() }),
  });

  const book = useMutation({
    mutationFn: async () => {
      const start = new Date(starts);
      const end = new Date(start.getTime() + 60 * 60 * 1000);
      return apiFetch("/api/v1/portal/sessions", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: home.data?.client_id,
          starts_at: start.toISOString(),
          ends_at: end.toISOString(),
          location: "Studio",
        }),
      });
    },
    onSuccess: () => {
      setStarts("");
      void qc.invalidateQueries({ queryKey: ["portal-sessions"] });
      void qc.invalidateQueries({ queryKey: ["portal-home"] });
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Book session</h1>
      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <Label htmlFor="starts">Start time</Label>
        <Input
          id="starts"
          type="datetime-local"
          value={starts}
          onChange={(e) => setStarts(e.target.value)}
        />
        <Button disabled={!starts || book.isPending} onClick={() => book.mutate()}>
          Request booking
        </Button>
      </div>
      <ul className="space-y-2">
        {(sessions.data ?? []).map((s) => (
          <li key={s.id} className="rounded-xl border border-forest/10 px-3 py-2 text-sm dark:border-sand/10">
            {new Date(s.starts_at).toLocaleString()} · {s.status}
          </li>
        ))}
      </ul>
    </section>
  );
}
