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

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-medium text-slate dark:text-sand/60">{greeting()}</p>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">{name}</h1>
        {me.data?.organization && (
          <p className="mt-1 text-sm text-slate dark:text-sand/60">{me.data.organization.name}</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Link to="/app/clients/new">
          <Button size="default">New client</Button>
        </Link>
        <Link to="/app/calendar?book=1">
          <Button variant="secondary">Book session</Button>
        </Link>
      </div>

      <div className="rounded-3xl bg-forest p-5 text-sand dark:bg-moss">
        <div className="flex items-center justify-between">
          <p className="font-display text-xl font-bold">Today&apos;s sessions</p>
          <Badge className="bg-lime/20 text-lime">
            {dash.data?.today_sessions.length ?? 0}
          </Badge>
        </div>
        <ul className="mt-4 space-y-3">
          {(dash.data?.today_sessions ?? []).length === 0 && (
            <li className="text-sm text-sand/80">No sessions scheduled today.</li>
          )}
          {(dash.data?.today_sessions ?? []).map((s) => (
            <li key={s.id}>
              <Link
                to={`/app/sessions/${s.id}`}
                className="flex items-center justify-between rounded-2xl bg-white/10 px-3 py-3"
              >
                <div>
                  <p className="font-semibold">{s.client_name ?? "Client"}</p>
                  <p className="text-xs text-sand/70">
                    {formatTime(s.starts_at)} · {s.status.replace("_", " ")}
                  </p>
                </div>
                <span className="text-sm text-lime">Open</span>
              </Link>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="font-display text-xl font-bold">Upcoming</h2>
        <ul className="mt-3 space-y-2">
          {(dash.data?.upcoming_sessions ?? []).slice(0, 5).map((s) => (
            <li key={s.id}>
              <Link
                to={`/app/sessions/${s.id}`}
                className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-3 py-3 dark:border-sand/10 dark:bg-white/5"
              >
                <span className="font-medium">{s.client_name}</span>
                <span className="text-sm text-slate dark:text-sand/60">
                  {new Date(s.starts_at).toLocaleString([], {
                    weekday: "short",
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </span>
              </Link>
            </li>
          ))}
          {(dash.data?.upcoming_sessions ?? []).length === 0 && (
            <p className="text-sm text-slate dark:text-sand/60">Nothing upcoming this week.</p>
          )}
        </ul>
      </div>

      <div>
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-bold">Recent clients</h2>
          <Link to="/app/clients" className="text-sm font-semibold text-moss dark:text-lime">
            View all
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
                  {c.remaining_credits ?? 0} credits
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
