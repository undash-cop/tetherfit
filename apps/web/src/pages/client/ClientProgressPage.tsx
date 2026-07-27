import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Assessment = {
  id: string;
  recorded_at: string;
  weight_kg: number | null;
  bmi: number | null;
};

export function ClientProgressPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["portal-progress"],
    queryFn: () =>
      apiFetch<Assessment[]>("/api/v1/portal/progress", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Progress</h1>
      <ul className="space-y-2">
        {(data ?? []).map((a) => (
          <li key={a.id} className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10">
            <p className="font-semibold">{new Date(a.recorded_at).toLocaleDateString()}</p>
            <p className="text-sm text-slate dark:text-sand/60">
              {a.weight_kg ?? "—"} kg · BMI {a.bmi ?? "—"}
            </p>
          </li>
        ))}
        {!data?.length && <p className="text-sm text-slate">No assessments yet.</p>}
      </ul>
    </section>
  );
}
