import { useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Input } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";

export function ClientsPage() {
  const [q, setQ] = useState("");
  const { data, isLoading, error } = useClients(q);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Clients</h1>
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
      <ul className="space-y-2">
        {(data?.items ?? []).map((client) => (
          <li key={client.id}>
            <Link
              to={`/app/clients/${client.id}`}
              className="flex items-center justify-between rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
            >
              <div>
                <p className="font-semibold">{client.full_name}</p>
                <p className="text-xs text-slate dark:text-sand/60">
                  {client.phone || client.email || "No contact"}
                </p>
              </div>
              <div className="text-right">
                <Badge>{client.status}</Badge>
                <p className="mt-1 text-xs text-slate dark:text-sand/60">
                  {client.remaining_credits ?? 0} left
                </p>
              </div>
            </Link>
          </li>
        ))}
      </ul>
      {data && data.items.length === 0 && (
        <p className="text-sm text-slate dark:text-sand/60">No clients yet. Add your first client.</p>
      )}
    </section>
  );
}
