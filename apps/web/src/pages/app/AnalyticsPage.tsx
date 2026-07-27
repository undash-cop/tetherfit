import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Point = { date: string; value: number };
type Analytics = {
  revenue_series: Point[];
  sessions_series: Point[];
  client_growth_series: Point[];
  completion_rate_pct: number;
  no_show_rate_pct: number;
  active_trainers: number;
};

export function AnalyticsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics"],
    queryFn: () =>
      apiFetch<Analytics>("/api/v1/analytics/overview?days=30", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  const sessions = (data?.sessions_series ?? []).map((p) => ({
    day: p.date.slice(5),
    sessions: p.value,
  }));
  const revenue = (data?.revenue_series ?? []).map((p) => ({
    day: p.date.slice(5),
    revenue: p.value / 100,
  }));

  return (
    <section className="space-y-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Analytics</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Session volume, revenue, completion, and team capacity.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Stat label="Completion" value={`${data?.completion_rate_pct ?? 0}%`} />
        <Stat label="No-shows" value={`${data?.no_show_rate_pct ?? 0}%`} />
        <Stat label="Trainers" value={data?.active_trainers ?? 0} />
      </div>

      <ChartCard title="Sessions (30d)">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={sessions}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="day" tick={{ fontSize: 11 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 11 }} width={28} />
            <Tooltip />
            <Bar dataKey="sessions" fill="#1f6b4f" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard title="Revenue ₹ (30d)">
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={revenue}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="day" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} width={36} />
            <Tooltip />
            <Bar dataKey="revenue" fill="#c8f560" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-2xl border border-forest/10 bg-white/70 p-3 dark:border-sand/10 dark:bg-white/5">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
        {label}
      </p>
      <p className="mt-1 font-display text-2xl font-bold text-forest dark:text-lime">{value}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
      <p className="mb-3 text-sm font-semibold">{title}</p>
      {children}
    </div>
  );
}
