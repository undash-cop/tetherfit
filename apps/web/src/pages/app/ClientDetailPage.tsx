import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Input, Label } from "@/components/ui/field";
import { useClient, useClientPackages, useCreatePackage } from "@/hooks/useClients";
import { useClientSessions } from "@/hooks/useSessions";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

export function ClientDetailPage() {
  const { id } = useParams();
  const client = useClient(id);
  const packages = useClientPackages(id);
  const history = useClientSessions(id);
  const createPkg = useCreatePackage(id!);
  const [sessions, setSessions] = useState(10);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "credits" | "sessions" | "notes">("overview");

  const invitePortal = useMutation({
    mutationFn: () =>
      apiFetch<{ token: string }>(`/api/v1/clients/${id}/portal-invite`, {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({}),
      }),
    onSuccess: (data) => setInviteToken(data.token),
  });

  const openChat = useMutation({
    mutationFn: () =>
      apiFetch<{ id: string }>(`/api/v1/chat/threads/${id}`, {
        method: "POST",
        token: getToken(),
      }),
  });

  if (client.isLoading) return <p>Loading…</p>;
  if (!client.data) return <p>Client not found.</p>;

  const c = client.data;

  return (
    <section className="space-y-4">
      <div>
        <Link to="/app/clients" className="text-sm font-semibold text-moss dark:text-lime">
          ← Clients
        </Link>
        <h1 className="mt-2 font-display text-3xl font-bold text-forest dark:text-lime">
          {c.full_name}
        </h1>
        <div className="mt-2 flex gap-2">
          <Badge>{c.status}</Badge>
          <Badge className="bg-moss/15 text-moss dark:bg-lime/15 dark:text-lime">
            {c.remaining_credits ?? 0} credits
          </Badge>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["overview", "credits", "sessions", "notes"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`min-h-10 rounded-xl px-3 text-sm font-semibold capitalize ${
              tab === t
                ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                : "bg-white/70 text-slate dark:bg-white/5 dark:text-sand/70"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
          <p>
            <span className="text-slate dark:text-sand/60">Phone:</span> {c.phone || "—"}
          </p>
          <p>
            <span className="text-slate dark:text-sand/60">Email:</span> {c.email || "—"}
          </p>
          <p>
            <span className="text-slate dark:text-sand/60">Goals:</span> {c.goals || "—"}
          </p>
          <p>
            <span className="text-slate dark:text-sand/60">Emergency:</span>{" "}
            {c.emergency_contact_name || "—"} {c.emergency_contact_phone || ""}
          </p>
          <Link to={`/app/calendar?book=1&client=${c.id}`}>
            <Button className="mt-2 w-full">Book session</Button>
          </Link>
          <Button
            className="w-full"
            variant="secondary"
            disabled={invitePortal.isPending}
            onClick={() => invitePortal.mutate()}
          >
            Invite to client portal
          </Button>
          {inviteToken && (
            <p className="break-all rounded-xl bg-sand/50 p-2 text-xs dark:bg-white/10">
              Invite token: {inviteToken}
            </p>
          )}
          <Button
            className="w-full"
            variant="outline"
            onClick={() => openChat.mutate()}
          >
            Open chat thread
          </Button>
          <Link to="/app/chat">
            <Button className="w-full" variant="ghost">
              Go to chat
            </Button>
          </Link>
        </div>
      )}

      {tab === "credits" && (
        <div className="space-y-4">
          <ul className="space-y-2">
            {(packages.data ?? []).map((p) => (
              <li
                key={p.id}
                className="rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
              >
                <p className="font-semibold">
                  {p.remaining_sessions} / {p.total_sessions} remaining
                </p>
                <p className="text-xs text-slate dark:text-sand/60">{p.notes || "Session pack"}</p>
              </li>
            ))}
          </ul>
          <div className="rounded-2xl border border-dashed border-forest/20 p-4 dark:border-sand/20">
            <Label htmlFor="pack">Grant package (sessions)</Label>
            <Input
              id="pack"
              type="number"
              min={1}
              value={sessions}
              onChange={(e) => setSessions(Number(e.target.value))}
            />
            <Button
              className="mt-3 w-full"
              disabled={createPkg.isPending}
              onClick={() => createPkg.mutate({ total_sessions: sessions, notes: "Manual pack" })}
            >
              Add credits
            </Button>
          </div>
        </div>
      )}

      {tab === "sessions" && (
        <ul className="space-y-2">
          {(history.data ?? []).length === 0 && (
            <p className="text-sm text-slate dark:text-sand/60">No sessions yet.</p>
          )}
          {(history.data ?? []).map((s) => (
            <li key={s.id}>
              <Link
                to={`/app/sessions/${s.id}`}
                className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
              >
                <div>
                  <p className="font-semibold">
                    {new Date(s.starts_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </p>
                  <p className="text-xs text-slate dark:text-sand/60">
                    {s.status.replace("_", " ")}
                    {s.credit_deducted ? " · credit used" : ""}
                  </p>
                </div>
                <span className="text-sm text-moss dark:text-lime">Open</span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {tab === "notes" && (
        <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
          <p>
            <span className="font-semibold">Health history</span>
            <br />
            {c.health_history || "—"}
          </p>
          <p>
            <span className="font-semibold">Medical notes</span>
            <br />
            {c.medical_notes || "—"}
          </p>
          <p>
            <span className="font-semibold">Notes</span>
            <br />
            {c.notes || "—"}
          </p>
        </div>
      )}
    </section>
  );
}
