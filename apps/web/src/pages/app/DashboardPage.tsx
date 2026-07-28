import { Link } from "react-router";

import { Badge } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { useDashboard } from "@/hooks/useSessions";
import { useMe } from "@/hooks/useMe";

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function DashboardPage() {
  const me = useMe();
  const dash = useDashboard();
  const name = me.data?.full_name || "Coach";
  const today = dash.data?.today_sessions ?? [];
  const clientsToday = new Set(today.map((s) => s.client_id)).size;
  const nextUp = today.find((s) => s.status === "scheduled" || s.status === "checked_in");

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-medium text-slate dark:text-sand/60">{greeting()}</p>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">{name}</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/60">
          Solo PT day · {me.data?.organization?.name || "your studio"}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-3xl bg-forest p-5 text-sand dark:bg-moss">
          <p className="text-xs uppercase tracking-wide text-sand/70">Sessions today</p>
          <p className="mt-1 font-display text-4xl font-bold text-lime">{today.length}</p>
        </div>
        <div className="rounded-3xl border border-forest/15 bg-white/80 p-5 dark:border-sand/15 dark:bg-white/5">
          <p className="text-xs uppercase tracking-wide text-slate dark:text-sand/60">
            PT clients today
          </p>
          <p className="mt-1 font-display text-4xl font-bold text-forest dark:text-lime">
            {clientsToday}
          </p>
        </div>
      </div>

      {nextUp && (
        <Link
          to={`/app/sessions/${nextUp.id}`}
          className="block rounded-3xl border border-moss/30 bg-moss/10 px-4 py-4 dark:border-lime/30 dark:bg-lime/10"
        >
          <p className="text-xs font-semibold uppercase tracking-wide text-moss dark:text-lime">
            Next up — tap to start
          </p>
          <p className="mt-1 font-display text-xl font-bold">
            {nextUp.client_name ?? "Client"} · {formatTime(nextUp.starts_at)}
          </p>
          <p className="text-sm text-slate dark:text-sand/70">GPS is recorded when you start</p>
        </Link>
      )}

      <div className="flex flex-wrap gap-2">
        <Link to="/app/clients/new">
          <Button>New client</Button>
        </Link>
        <Link to="/app/calendar?book=1">
          <Button variant="secondary">Book session</Button>
        </Link>
        <Link to="/app/payments">
          <Button variant="outline">Payments / GST</Button>
        </Link>
      </div>

      <div className="rounded-3xl border border-forest/10 bg-white/70 p-5 dark:border-sand/10 dark:bg-white/5">
        <div className="flex items-center justify-between">
          <p className="font-display text-xl font-bold">Today&apos;s sessions</p>
          <Badge>{today.length}</Badge>
        </div>
        <ul className="mt-4 space-y-3">
          {today.length === 0 && (
            <li className="text-sm text-slate dark:text-sand/70">No sessions scheduled today.</li>
          )}
          {today.map((s) => (
            <li key={s.id}>
              <Link
                to={`/app/sessions/${s.id}`}
                className="flex items-center justify-between rounded-2xl bg-fog px-3 py-3 dark:bg-white/5"
              >
                <div>
                  <p className="font-semibold">{s.client_name ?? "Client"}</p>
                  <p className="text-xs text-slate dark:text-sand/70">
                    {formatTime(s.starts_at)} · {s.status.replace("_", " ")}
                  </p>
                </div>
                <span className="text-sm font-semibold text-moss dark:text-lime">Open</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-bold">Recent clients</h2>
          <Link to="/app/clients" className="text-sm font-semibold text-moss dark:text-lime">
            All clients
          </Link>
        </div>
        <ul className="mt-3 space-y-2">
          {(dash.data?.recent_clients ?? []).map((c) => (
            <li key={c.id}>
              <Link
                to={`/app/clients/${c.id}`}
                className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-3 py-3 dark:border-sand/10 dark:bg-white/5"
              >
                <span className="font-medium">{c.full_name}</span>
                <span className="text-sm text-slate dark:text-sand/60">
                  {c.remaining_credits ?? 0} left
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
