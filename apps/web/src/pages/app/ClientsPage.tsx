import { useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Input } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";

function formatMoney(paise: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" });
}

export function ClientsPage() {
  const [q, setQ] = useState("");
  const { data, isLoading, error } = useClients(q);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Clients</h1>
          <p className="text-sm text-slate dark:text-sand/70">
            PT period, paid amount, sessions completed
          </p>
        </div>
        <Link to="/app/clients/new">
          <Button>Add</Button>
        </Link>
      </div>
      <Input
        placeholder="Search name, email, phone…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {isLoading && <p className="text-sm text-slate">Loading…</p>}
      {error && (
        <p className="text-sm text-red-700">Could not load clients. Check API auth and org setup.</p>
      )}
      <ul className="space-y-3">
        {(data?.items ?? []).map((client) => (
          <li
            key={client.id}
            className="rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
          >
            <Link to={`/app/clients/${client.id}`} className="block">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{client.full_name}</p>
                  <p className="text-xs text-slate dark:text-sand/60">
                    Joined {formatDate(client.joined_on ?? client.created_at)}
                  </p>
                </div>
                <Badge>{client.status}</Badge>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate dark:text-sand/70 sm:grid-cols-4">
                <div>
                  <p className="uppercase tracking-wide opacity-70">PT start</p>
                  <p className="font-semibold text-forest dark:text-sand">
                    {formatDate(client.pt_start_at)}
                  </p>
                </div>
                <div>
                  <p className="uppercase tracking-wide opacity-70">PT end</p>
                  <p className="font-semibold text-forest dark:text-sand">
                    {formatDate(client.pt_end_at)}
                  </p>
                </div>
                <div>
                  <p className="uppercase tracking-wide opacity-70">Amount paid</p>
                  <p className="font-semibold text-forest dark:text-sand">
                    {formatMoney(client.amount_paid_paise ?? 0)}
                  </p>
                </div>
                <div>
                  <p className="uppercase tracking-wide opacity-70">Sessions done</p>
                  <p className="font-semibold text-forest dark:text-sand">
                    {client.sessions_completed ?? 0}
                  </p>
                </div>
              </div>
            </Link>
            <div className="mt-3 flex flex-wrap gap-2 border-t border-forest/10 pt-3 dark:border-sand/10">
              <Link to={`/app/clients/${client.id}?action=schedule`}>
                <Button size="default" variant="secondary">
                  Schedule
                </Button>
              </Link>
              <Link to={`/app/clients/${client.id}?action=invoice`}>
                <Button size="default" variant="outline">
                  Generate invoice
                </Button>
              </Link>
              <Link to={`/app/clients/${client.id}?tab=sessions`}>
                <Button size="default" variant="ghost">
                  Cancel session
                </Button>
              </Link>
            </div>
          </li>
        ))}
      </ul>
      {data && data.items.length === 0 && (
        <p className="text-sm text-slate dark:text-sand/60">No clients yet. Add your first client.</p>
      )}
    </section>
  );
}
