import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Usage = {
  organizations: number;
  users: number;
  clients: number;
  sessions_30d: number;
};

export function AdminUsagePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-usage"],
    queryFn: () => apiFetch<Usage>("/api/v1/admin/usage", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  const cards = [
    { label: "Organizations", value: data?.organizations ?? 0 },
    { label: "Users", value: data?.users ?? 0 },
    { label: "Clients", value: data?.clients ?? 0 },
    { label: "Sessions (30d)", value: data?.sessions_30d ?? 0 },
  ];

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Platform usage</h1>
      <div className="grid gap-3 sm:grid-cols-2">
        {cards.map((c) => (
          <div key={c.label} className="rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
            <p className="text-xs font-semibold uppercase text-slate dark:text-sand/60">{c.label}</p>
            <p className="mt-2 font-display text-3xl font-bold">{c.value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
