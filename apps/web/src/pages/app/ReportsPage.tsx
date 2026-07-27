import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Reports = {
  clients_total: number;
  clients_active: number;
  sessions_completed_30d: number;
  sessions_scheduled_upcoming: number;
  revenue_paise_30d: number;
  outstanding_paise: number;
  generated_at: string;
};

function money(paise: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

export function ReportsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["reports"],
    queryFn: () => apiFetch<Reports>("/api/v1/reports/summary", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  const cards = [
    { label: "Active clients", value: data?.clients_active ?? 0 },
    { label: "Total clients", value: data?.clients_total ?? 0 },
    { label: "Sessions (30d)", value: data?.sessions_completed_30d ?? 0 },
    { label: "Upcoming sessions", value: data?.sessions_scheduled_upcoming ?? 0 },
    { label: "Revenue (30d)", value: money(data?.revenue_paise_30d ?? 0) },
    { label: "Outstanding", value: money(data?.outstanding_paise ?? 0) },
  ];

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Reports</h1>
      <p className="text-sm text-slate dark:text-sand/70">Business snapshot for the last 30 days.</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {cards.map((c) => (
          <div
            key={c.label}
            className="rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5"
          >
            <p className="text-xs font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
              {c.label}
            </p>
            <p className="mt-2 font-display text-3xl font-bold text-forest dark:text-lime">
              {c.value}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
