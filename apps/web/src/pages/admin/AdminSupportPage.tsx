import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Ticket = {
  id: string;
  subject: string;
  body: string;
  status: string;
  priority: string;
};

export function AdminSupportPage() {
  const qc = useQueryClient();
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const tickets = useQuery({
    queryKey: ["admin-tickets"],
    queryFn: () => apiFetch<Ticket[]>("/api/v1/admin/tickets", { token: getToken() }),
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/admin/tickets", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ subject, body }),
      }),
    onSuccess: () => {
      setSubject("");
      setBody("");
      void qc.invalidateQueries({ queryKey: ["admin-tickets"] });
    },
  });

  const resolve = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/admin/tickets/${id}?status_value=resolved`, {
        method: "PATCH",
        token: getToken(),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["admin-tickets"] }),
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Support</h1>
      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <Label>Subject</Label>
        <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
        <Label>Body</Label>
        <Input value={body} onChange={(e) => setBody(e.target.value)} />
        <Button disabled={!subject || !body} onClick={() => create.mutate()}>
          Open ticket
        </Button>
      </div>
      <ul className="space-y-2">
        {(tickets.data ?? []).map((t) => (
          <li
            key={t.id}
            className="flex items-start justify-between gap-2 rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <div>
              <p className="font-semibold">
                {t.subject} · {t.status}
              </p>
              <p className="text-sm text-slate dark:text-sand/70">{t.body}</p>
            </div>
            {t.status !== "resolved" && (
              <Button variant="outline" onClick={() => resolve.mutate(t.id)}>
                Resolve
              </Button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
