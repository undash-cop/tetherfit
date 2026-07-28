import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge, Input, Label } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";
import { useMe } from "@/hooks/useMe";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Invoice = {
  id: string;
  invoice_number: string;
  client_id: string;
  status: string;
  total_paise: number;
  tax_paise?: number;
  currency: string;
};
type Payment = {
  id: string;
  amount_paise: number;
  status: string;
  provider: string;
  method?: string | null;
  invoice_id: string | null;
  checkout?: Record<string, unknown>;
};
type UpiQr = {
  upi_vpa: string;
  upi_uri: string;
  qr_image_url: string;
  amount_paise: number;
  invoice_number: string;
};

function formatMoney(paise: number, currency = "INR") {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

async function openGstInvoice(invoiceId: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const res = await fetch(`${base}/api/v1/invoices/${invoiceId}/gst-invoice`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const htmlDoc = await res.text();
  const blob = new Blob([htmlDoc], { type: "text/html" });
  window.open(URL.createObjectURL(blob), "_blank");
}

export function PaymentsPage() {
  const me = useMe();
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
  const [qr, setQr] = useState<UpiQr | null>(null);
  const [qrInvoiceId, setQrInvoiceId] = useState<string | null>(null);

  const gstPct = me.data?.organization?.default_gst_pct ?? 0;

  const createInvoice = useMutation({
    mutationFn: () =>
      apiFetch<Invoice>("/api/v1/invoices", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: clientId,
          line_items: [{ description: "Training package", quantity: 1, unit_paise: amount * 100 }],
          apply_default_gst: true,
        }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["invoices"] }),
  });

  const collectUpi = useMutation({
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
      setQr(null);
      setQrInvoiceId(null);
      void qc.invalidateQueries({ queryKey: ["payments"] });
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  const collectCash = useMutation({
    mutationFn: (invoiceId: string) =>
      apiFetch<Payment>("/api/v1/payments/cash", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ invoice_id: invoiceId }),
      }),
    onSuccess: () => {
      setQr(null);
      setQrInvoiceId(null);
      void qc.invalidateQueries({ queryKey: ["payments"] });
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });

  const showQr = useMutation({
    mutationFn: (invoiceId: string) =>
      apiFetch<UpiQr>(`/api/v1/invoices/${invoiceId}/upi-qr`, { token: getToken() }),
    onSuccess: (data, invoiceId) => {
      setQr(data);
      setQrInvoiceId(invoiceId);
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Payments</h1>

      <div className="rounded-3xl bg-forest p-5 text-sand dark:bg-moss">
        <p className="text-sm text-sand/70">Collect with QR or cash · GST invoices</p>
        <p className="font-display text-2xl font-bold text-lime">Payments</p>
        {gstPct > 0 && (
          <p className="mt-2 text-xs text-sand/70">Default GST {gstPct}% applied on new invoices</p>
        )}
      </div>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">1. Create GST invoice</h2>
        <p className="text-xs text-slate dark:text-sand/60">
          Invoice creation is independent of payment. Collect cash/QR later if needed.
        </p>
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
        <Label>Amount before GST (INR)</Label>
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

      {qr && (
        <div className="space-y-3 rounded-2xl border border-moss/30 bg-moss/5 p-4 dark:border-lime/30">
          <h2 className="font-display text-xl font-bold">UPI QR · {qr.invoice_number}</h2>
          <p className="text-sm text-slate dark:text-sand/70">
            Pay {formatMoney(qr.amount_paise)} to {qr.upi_vpa}
          </p>
          <img
            src={qr.qr_image_url}
            alt="UPI QR code"
            className="mx-auto h-56 w-56 rounded-xl bg-white p-2"
          />
          {qrInvoiceId && (
            <Button
              className="w-full"
              disabled={collectUpi.isPending}
              onClick={() => collectUpi.mutate(qrInvoiceId)}
            >
              Mark UPI received
            </Button>
          )}
        </div>
      )}

      <h2 className="font-display text-xl font-bold">2. Invoices</h2>
      <p className="text-xs text-slate dark:text-sand/60 -mt-2">
        View GST anytime. Cash/QR collect is optional and separate.
      </p>
      <ul className="space-y-2">
        {(invoices.data ?? []).map((inv) => (
          <li
            key={inv.id}
            className="space-y-2 rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
          >
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="font-semibold">{inv.invoice_number}</p>
                <p className="text-sm text-slate dark:text-sand/60">
                  {formatMoney(inv.total_paise, inv.currency)}
                  {inv.tax_paise ? ` · GST ${formatMoney(inv.tax_paise)}` : ""}
                </p>
              </div>
              <Badge>{inv.status}</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => void openGstInvoice(inv.id)}>
                View GST invoice
              </Button>
              {inv.status !== "paid" && (
                <>
                  <Button
                    variant="secondary"
                    disabled={showQr.isPending}
                    onClick={() => showQr.mutate(inv.id)}
                  >
                    Show QR
                  </Button>
                  <Button
                    disabled={collectCash.isPending}
                    onClick={() => collectCash.mutate(inv.id)}
                  >
                    Cash received
                  </Button>
                  <Button
                    variant="ghost"
                    disabled={collectUpi.isPending}
                    onClick={() => collectUpi.mutate(inv.id)}
                  >
                    Confirm UPI
                  </Button>
                </>
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
              {p.method || p.provider} · {p.status}
            </Badge>
          </li>
        ))}
      </ul>
    </section>
  );
}
