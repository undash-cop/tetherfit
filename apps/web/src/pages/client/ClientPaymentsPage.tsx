import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Invoice = {
  id: string;
  invoice_number: string;
  status: string;
  total_paise: number;
  currency: string;
};

function money(paise: number, currency: string) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

export function ClientPaymentsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["portal-payments"],
    queryFn: () => apiFetch<Invoice[]>("/api/v1/portal/payments", { token: getToken() }),
  });

  if (isLoading) return <p>Loading…</p>;

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Payments</h1>
      <ul className="space-y-2">
        {(data ?? []).map((i) => (
          <li key={i.id} className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10">
            <p className="font-semibold">{i.invoice_number}</p>
            <p className="text-sm">
              {money(i.total_paise, i.currency)} · {i.status}
            </p>
          </li>
        ))}
        {!data?.length && <p className="text-sm text-slate">No invoices yet.</p>}
      </ul>
    </section>
  );
}
