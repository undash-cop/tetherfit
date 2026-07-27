import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Plan = {
  id: string;
  name: string;
  calories: number | null;
  protein_g: number | null;
  meals: { name?: string; items?: string[] }[];
};

export function ClientNutritionPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["portal-nutrition"],
    queryFn: () => apiFetch<Plan[]>("/api/v1/portal/nutrition", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Nutrition</h1>
      {(data ?? []).map((p) => (
        <div key={p.id} className="rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
          <p className="font-semibold">{p.name}</p>
          <p className="text-sm text-slate dark:text-sand/60">
            {p.calories ?? "—"} kcal · P {p.protein_g ?? "—"}g
          </p>
          <ul className="mt-2 text-sm">
            {(p.meals ?? []).map((m, i) => (
              <li key={i}>
                <span className="font-medium">{m.name}</span>: {(m.items ?? []).join(", ")}
              </li>
            ))}
          </ul>
        </div>
      ))}
      {!data?.length && <p className="text-sm text-slate">No meal plans yet.</p>}
    </section>
  );
}
