import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Org = {
  id: string;
  name: string;
  slug: string;
  plan: string;
  subscription_status: string;
  users_count: number;
  clients_count: number;
};

export function AdminOrgsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["admin-orgs"],
    queryFn: () => apiFetch<Org[]>("/api/v1/admin/organizations", { token: getToken() }),
  });

  const suspend = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/api/v1/admin/organizations/${id}`, {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify({ subscription_status: "suspended" }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["admin-orgs"] }),
  });

  if (isLoading) return <p>Loading…</p>;

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Organizations</h1>
      <ul className="space-y-2">
        {(data ?? []).map((o) => (
          <li
            key={o.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <div>
              <p className="font-semibold">
                {o.name} · {o.slug}
              </p>
              <p className="text-sm text-slate dark:text-sand/60">
                {o.plan} · {o.subscription_status} · {o.users_count} users · {o.clients_count}{" "}
                clients
              </p>
            </div>
            <Button variant="outline" onClick={() => suspend.mutate(o.id)}>
              Suspend
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}
