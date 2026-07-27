import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge, Input, Label } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";
import { useDashboard } from "@/hooks/useSessions";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Invoice = {
  id: string;
  invoice_number: string;
  client_id: string;
  status: string;
  total_paise: number;
  currency: string;
};
type Payment = {
  id: string;
  amount_paise: number;
  status: string;
  provider: string;
  invoice_id: string | null;
  checkout?: Record<string, unknown>;
};

function formatMoney(paise: number, currency = "INR") {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

export function PaymentsPage() {
  const dash = useDashboard();
  const clients = useClients();
  const qc = useQueryClient();
  const invoices = useQuery({
    queryKey: ["invoices"],
    queryFn: () => apiFetch<Invoice[]>("/api/v1/invoices", { token: getToken() }),
  });
  const payments = useQuery({
    queryKey: ["payments"],
    queryFn: () => apiFetch<Payment[]>("/api/v1/payments", { token: getToken() }),
  });

  const [clientId, setClientId] = useState("");
  const [amount, setAmount] = useState(5000);

  const createInvoice = useMutation({
    mutationFn: () =>
      apiFetch<Invoice>("/api/v1/invoices", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: clientId,
          line_items: [{ description: "Training package", quantity: 1, unit_paise: amount * 100 }],
          tax_paise: 0,
        }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["invoices"] }),
  });

  const collect = useMutation({
    mutationFn: async (invoiceId: string) => {
      const payment = await apiFetch<Payment>("/api/v1/payments/collect", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ invoice_id: invoiceId }),
      });
      await apiFetch("/api/v1/payments/confirm", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          payment_id: payment.id,
          provider_payment_id: `pay_${Date.now()}`,
          method: "upi",
        }),
      });
      return payment;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["payments"] });
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Payments</h1>

      <div className="rounded-3xl bg-forest p-5 text-sand dark:bg-moss">
        <p className="text-sm text-sand/70">Session credits remaining</p>
        <p className="font-display text-4xl font-bold text-lime">
          {dash.data?.total_remaining_credits ?? 0}
        </p>
      </div>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Create invoice</h2>
        <Label>Client</Label>
        <select
          className="min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm dark:bg-white/5"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
        >
          <option value="">Select…</option>
          {(clients.data?.items ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name}
            </option>
          ))}
        </select>
        <Label>Amount (INR)</Label>
        <Input
          type="number"
          value={amount}
          onChange={(e) => setAmount(Number(e.target.value))}
        />
        <Button
          disabled={!clientId || createInvoice.isPending}
          onClick={() => createInvoice.mutate()}
        >
          Create invoice
        </Button>
      </div>

      <h2 className="font-display text-xl font-bold">Invoices</h2>
      <ul className="space-y-2">
        {(invoices.data ?? []).map((inv) => (
          <li
            key={inv.id}
            className="flex items-center justify-between rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
          >
            <div>
              <p className="font-semibold">{inv.invoice_number}</p>
              <p className="text-sm text-slate dark:text-sand/60">
                {formatMoney(inv.total_paise, inv.currency)}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge>{inv.status}</Badge>
              {inv.status !== "paid" && (
                <Button
                  size="default"
                  disabled={collect.isPending}
                  onClick={() => collect.mutate(inv.id)}
                >
                  Collect
                </Button>
              )}
            </div>
          </li>
        ))}
      </ul>

      <h2 className="font-display text-xl font-bold">Payment history</h2>
      <ul className="space-y-2">
        {(payments.data ?? []).map((p) => (
          <li
            key={p.id}
            className="flex justify-between rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <span>{formatMoney(p.amount_paise)}</span>
            <Badge>
              {p.provider} · {p.status}
            </Badge>
          </li>
        ))}
      </ul>

      <h2 className="font-display text-xl font-bold">Low credit clients</h2>
      <ul className="space-y-2">
        {(dash.data?.low_credit_clients ?? []).map((c) => (
          <li key={c.client_id} className="flex justify-between text-sm">
            <span>{c.client_name}</span>
            <Badge>{c.remaining_sessions} left</Badge>
          </li>
        ))}
      </ul>
    </section>
  );
}
