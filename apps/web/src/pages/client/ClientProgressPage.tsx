import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Assessment = {
  id: string;
  recorded_at: string;
  weight_kg: number | null;
  bmi: number | null;
  photo_urls: string[];
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
            {a.photo_urls?.length > 0 && (
              <div className="mt-2 flex gap-2 overflow-x-auto">
                {a.photo_urls.map((url) => (
                  <img
                    key={url}
                    src={url}
                    alt="Progress photo"
                    className="h-24 w-24 rounded-xl object-cover"
                  />
                ))}
              </div>
            )}
          </li>
        ))}
        {!data?.length && <p className="text-sm text-slate">No assessments yet.</p>}
      </ul>
    </section>
  );
}
