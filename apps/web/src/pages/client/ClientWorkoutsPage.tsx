import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Workout = {
  assignment_id: string;
  plan_name: string;
  items: { name?: string; sets?: number; reps?: string }[];
};

export function ClientWorkoutsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["portal-workouts"],
    queryFn: () => apiFetch<Workout[]>("/api/v1/portal/workouts", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Workouts</h1>
      <ul className="space-y-3">
        {(data ?? []).map((w) => (
          <li
            key={w.assignment_id}
            className="rounded-2xl border border-forest/10 p-4 dark:border-sand/10"
          >
            <p className="font-semibold">{w.plan_name}</p>
            <ul className="mt-2 space-y-1 text-sm text-slate dark:text-sand/70">
              {(w.items ?? []).slice(0, 6).map((i, idx) => (
                <li key={idx}>
                  {i.name || "Exercise"}
                  {i.sets ? ` · ${i.sets}×${i.reps ?? ""}` : ""}
                </li>
              ))}
            </ul>
          </li>
        ))}
        {!data?.length && <p className="text-sm text-slate">No assigned workouts yet.</p>}
      </ul>
    </section>
  );
}
