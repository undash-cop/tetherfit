import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Input, Label } from "@/components/ui/field";
import { useClient, useUpdateClient } from "@/hooks/useClients";
import { useCancelSession, useClientSessions } from "@/hooks/useSessions";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Assessment = {
  id: string;
  recorded_at: string;
  weight_kg: number | null;
  height_cm: number | null;
  bmi: number | null;
  photo_urls: string[];
};

type Presign = {
  asset_id: string;
  upload_url: string;
  public_url: string | null;
  headers: Record<string, string>;
  object_key: string;
};

type Invoice = {
  id: string;
  invoice_number: string;
  client_id: string;
  status: string;
  total_paise: number;
  tax_paise?: number;
  currency?: string;
};

type UpiQr = {
  upi_vpa: string;
  qr_image_url: string;
  amount_paise: number;
  invoice_number: string;
};

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

function ptValidityLabel(code: string | undefined) {
  switch (code) {
    case "active":
      return "Active";
    case "upcoming":
      return "Upcoming";
    case "expired":
      return "Expired";
    default:
      return "Not set";
  }
}

function ptValidityDetail(
  code: string | undefined,
  start: string | null | undefined,
  end: string | null | undefined,
) {
  if (code === "upcoming") return `Starts ${formatDate(start)}`;
  if (code === "expired") return `Ended ${formatDate(end)}`;
  if (code === "active") return `${formatDate(start)} → ${formatDate(end)}`;
  return "Set PT start and end dates";
}

async function openGstInvoice(invoiceId: string) {
  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  const res = await fetch(`${base}/api/v1/invoices/${invoiceId}/gst-invoice`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) throw new Error("Could not open GST invoice");
  const htmlDoc = await res.text();
  const blob = new Blob([htmlDoc], { type: "text/html" });
  window.open(URL.createObjectURL(blob), "_blank");
}

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function ClientDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const client = useClient(id);
  const history = useClientSessions(id);
  const updateClient = useUpdateClient(id!);
  const cancelSession = useCancelSession();
  const qc = useQueryClient();

  const [weight, setWeight] = useState(70);
  const [height, setHeight] = useState(170);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [scheduleStarts, setScheduleStarts] = useState("");
  const [scheduleWeekday, setScheduleWeekday] = useState(0);
  const [scheduleDuration, setScheduleDuration] = useState(60);
  const [invoiceAmount, setInvoiceAmount] = useState(5000);
  const [ptStart, setPtStart] = useState("");
  const [ptEnd, setPtEnd] = useState("");
  const [lastInvoiceId, setLastInvoiceId] = useState<string | null>(null);
  const [qr, setQr] = useState<UpiQr | null>(null);
  const [qrInvoiceId, setQrInvoiceId] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "payments" | "sessions" | "assessments" | "notes">(
    "overview",
  );
  const [focusPanel, setFocusPanel] = useState<"schedule" | "invoice" | null>(null);

  useEffect(() => {
    const action = searchParams.get("action");
    const tabParam = searchParams.get("tab");
    if (tabParam === "sessions") {
      setTab("sessions");
      setFocusPanel(null);
    } else if (tabParam === "payments" || action === "invoice") {
      setTab("payments");
      setFocusPanel(action === "invoice" ? "invoice" : null);
    } else if (action === "schedule") {
      setTab("overview");
      setFocusPanel("schedule");
    }
  }, [searchParams]);

  useEffect(() => {
    if (!client.data) return;
    setPtStart(client.data.pt_start_at ? client.data.pt_start_at.slice(0, 10) : "");
    setPtEnd(client.data.pt_end_at ? client.data.pt_end_at.slice(0, 10) : "");
  }, [client.data]);

  const assessments = useQuery({
    queryKey: ["assessments", id],
    queryFn: () =>
      apiFetch<Assessment[]>(`/api/v1/assessments?client_id=${id}`, { token: getToken() }),
    enabled: Boolean(id),
  });

  const invoices = useQuery({
    queryKey: ["invoices", "client", id],
    queryFn: () =>
      apiFetch<Invoice[]>(`/api/v1/invoices?client_id=${id}`, { token: getToken() }),
    enabled: Boolean(id),
  });

  const clientInvoices = invoices.data ?? [];


  const scheduleSeries = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/recurrence-rules", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: id,
          frequency: "weekly",
          byweekday: [scheduleWeekday],
          starts_on: new Date(scheduleStarts).toISOString(),
          duration_minutes: scheduleDuration,
          generate_weeks: 8,
        }),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["recurrence-rules"] });
      void qc.invalidateQueries({ queryKey: ["calendar"] });
      void qc.invalidateQueries({ queryKey: ["sessions", "client", id] });
    },
  });

  const createInvoice = useMutation({
    mutationFn: () =>
      apiFetch<Invoice>("/api/v1/invoices", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: id,
          line_items: [
            { description: "Personal training", quantity: 1, unit_paise: invoiceAmount * 100 },
          ],
          apply_default_gst: true,
        }),
      }),
    onSuccess: (inv) => {
      setLastInvoiceId(inv.id);
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["invoices", "client", id] });
    },
  });

  const collectCash = useMutation({
    mutationFn: (invoiceId: string) =>
      apiFetch("/api/v1/payments/cash", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ invoice_id: invoiceId }),
      }),
    onSuccess: () => {
      setQr(null);
      setQrInvoiceId(null);
      void qc.invalidateQueries({ queryKey: ["payments"] });
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["invoices", "client", id] });
      void qc.invalidateQueries({ queryKey: ["clients"] });
      void qc.invalidateQueries({ queryKey: ["clients", id] });
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

  const markUpi = useMutation({
    mutationFn: async (invoiceId: string) => {
      const payment = await apiFetch<{ id: string }>("/api/v1/payments/collect", {
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
    },
    onSuccess: () => {
      setQr(null);
      setQrInvoiceId(null);
      void qc.invalidateQueries({ queryKey: ["payments"] });
      void qc.invalidateQueries({ queryKey: ["invoices"] });
      void qc.invalidateQueries({ queryKey: ["invoices", "client", id] });
      void qc.invalidateQueries({ queryKey: ["clients"] });
      void qc.invalidateQueries({ queryKey: ["clients", id] });
    },
  });

  const addAssessment = useMutation({
    mutationFn: async () => {
      const photoUrls: string[] = [];
      if (photoFile) {
        const presign = await apiFetch<Presign>("/api/v1/media/presign", {
          method: "POST",
          token: getToken(),
          body: JSON.stringify({
            filename: photoFile.name,
            content_type: photoFile.type || "image/jpeg",
            kind: "transformation",
            client_id: id,
            size_bytes: photoFile.size,
          }),
        });
        if (presign.upload_url.startsWith("http")) {
          await fetch(presign.upload_url, {
            method: "PUT",
            headers: presign.headers,
            body: photoFile,
          });
        }
        photoUrls.push(presign.public_url || `https://media.local/${presign.object_key}`);
      }
      return apiFetch("/api/v1/assessments", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: id,
          recorded_at: new Date().toISOString(),
          weight_kg: weight,
          height_cm: height,
          photo_urls: photoUrls,
          measurements: {},
        }),
      });
    },
    onSuccess: () => {
      setPhotoFile(null);
      void qc.invalidateQueries({ queryKey: ["assessments", id] });
    },
  });

  if (client.isLoading) return <p>Loading…</p>;
  if (!client.data) return <p>Client not found.</p>;

  const c = client.data;
  const validityCode = c.pt_validity;
  const validityLabel = ptValidityLabel(validityCode);
  const validityDetail = ptValidityDetail(validityCode, c.pt_start_at, c.pt_end_at);
  const cancellable = (history.data ?? []).filter(
    (s) => s.status === "scheduled" || s.status === "checked_in",
  );

  return (
    <section className="space-y-4">
      <div>
        <Link to="/app/clients" className="text-sm font-semibold text-moss dark:text-lime">
          ← Clients
        </Link>
        <h1 className="mt-2 font-display text-3xl font-bold text-forest dark:text-lime">
          {c.full_name}
        </h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          {c.phone || c.email || "No contact"} · Joined {formatDate(c.joined_on ?? c.created_at)}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <SummaryTile
          label="PT validity"
          value={validityLabel}
          hint={validityDetail}
          accent={validityCode === "active"}
        />
        <SummaryTile
          label="Payments collected"
          value={formatMoney(c.amount_paid_paise ?? 0)}
          hint="Paid invoices only"
        />
        <SummaryTile
          label="Sessions done"
          value={String(c.sessions_completed ?? 0)}
          hint="Completed PT sessions"
        />
        <SummaryTile label="Status" value={c.status} hint={c.goals || "No goals set"} />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          onClick={() => {
            setTab("overview");
            setFocusPanel("schedule");
          }}
        >
          Schedule
        </Button>
        <Button
          variant="outline"
          onClick={() => {
            setTab("payments");
            setFocusPanel("invoice");
          }}
        >
          Generate invoice
        </Button>
        <Button variant="ghost" onClick={() => setTab("sessions")}>
          Cancel session
        </Button>
        <Link to={`/app/calendar?book=1&client=${c.id}`}>
          <Button variant="ghost">Book once</Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["overview", "payments", "sessions", "assessments", "notes"] as const).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`min-h-10 rounded-xl px-3 text-sm font-semibold capitalize ${
              tab === t
                ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                : "bg-white/70 text-slate dark:bg-white/5 dark:text-sand/70"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="space-y-4">
          <div className="space-y-2 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
            <h2 className="font-display text-lg font-bold">PT validity</h2>
            <p className="text-sm text-slate dark:text-sand/70">
              {validityLabel}: {validityDetail}
            </p>
            <Label>PT start</Label>
            <Input type="date" value={ptStart} onChange={(e) => setPtStart(e.target.value)} />
            <Label>PT end</Label>
            <Input type="date" value={ptEnd} onChange={(e) => setPtEnd(e.target.value)} />
            <Button
              className="w-full"
              variant="outline"
              disabled={updateClient.isPending}
              onClick={() =>
                updateClient.mutate({
                  pt_start_at: ptStart ? new Date(ptStart).toISOString() : null,
                  pt_end_at: ptEnd ? new Date(ptEnd).toISOString() : null,
                })
              }
            >
              Save PT validity
            </Button>
          </div>

          <div
            className={`space-y-2 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5 ${
              focusPanel === "schedule" ? "ring-2 ring-moss/40" : ""
            }`}
          >
            <h2 className="font-display text-lg font-bold">Schedule series</h2>
            <p className="text-xs text-slate dark:text-sand/60">
              Frequency (weekday) + duration → generate upcoming classes.
            </p>
            <Label>First session</Label>
            <Input
              type="datetime-local"
              value={scheduleStarts}
              onChange={(e) => setScheduleStarts(e.target.value)}
            />
            <Label>Duration (minutes)</Label>
            <Input
              type="number"
              min={15}
              value={scheduleDuration}
              onChange={(e) => setScheduleDuration(Number(e.target.value))}
            />
            <Label>Weekday</Label>
            <div className="flex flex-wrap gap-2">
              {days.map((d, i) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setScheduleWeekday(i)}
                  className={`min-h-10 rounded-xl px-3 text-sm font-semibold ${
                    scheduleWeekday === i
                      ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                      : "bg-white/70 dark:bg-white/5"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <Button
              className="w-full"
              disabled={!scheduleStarts || scheduleSeries.isPending}
              onClick={() => scheduleSeries.mutate()}
            >
              Schedule weekly series
            </Button>
          </div>
        </div>
      )}

      {tab === "payments" && (
        <div className="space-y-4">
          <div
            className={`space-y-2 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5 ${
              focusPanel === "invoice" ? "ring-2 ring-moss/40" : ""
            }`}
          >
            <h2 className="font-display text-lg font-bold">1. Generate GST invoice</h2>
            <p className="text-xs text-slate dark:text-sand/60">
              Creating an invoice does not require collecting payment. You can view/print GST anytime.
            </p>
            <Label>Amount before GST (INR)</Label>
            <Input
              type="number"
              value={invoiceAmount}
              onChange={(e) => setInvoiceAmount(Number(e.target.value))}
            />
            <Button
              className="w-full"
              disabled={createInvoice.isPending || invoiceAmount <= 0}
              onClick={() => createInvoice.mutate()}
            >
              {createInvoice.isPending ? "Creating…" : "Create GST invoice"}
            </Button>
            {lastInvoiceId && (
              <Button
                className="w-full"
                variant="outline"
                onClick={() => void openGstInvoice(lastInvoiceId)}
              >
                View / print GST invoice
              </Button>
            )}
          </div>

          {qr && (
            <div className="space-y-2 rounded-2xl border border-moss/30 bg-moss/5 p-4 dark:border-lime/30">
              <h2 className="font-display text-lg font-bold">UPI QR · {qr.invoice_number}</h2>
              <p className="text-sm text-slate dark:text-sand/70">
                {formatMoney(qr.amount_paise)} → {qr.upi_vpa}
              </p>
              <img
                src={qr.qr_image_url}
                alt="UPI QR"
                className="mx-auto h-52 w-52 rounded-xl bg-white p-2"
              />
              {qrInvoiceId && (
                <Button
                  className="w-full"
                  disabled={markUpi.isPending}
                  onClick={() => markUpi.mutate(qrInvoiceId)}
                >
                  Mark UPI received
                </Button>
              )}
            </div>
          )}

          <div className="space-y-2">
            <h2 className="font-display text-lg font-bold">Invoices for this client</h2>
            <p className="text-xs text-slate dark:text-sand/60">
              GST invoice is always available. Collect cash/QR only when you want to mark payment.
            </p>
            {clientInvoices.length === 0 && (
              <p className="text-sm text-slate dark:text-sand/60">No invoices yet.</p>
            )}
            <ul className="space-y-2">
              {clientInvoices.map((inv) => (
                <li
                  key={inv.id}
                  className="space-y-2 rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold">{inv.invoice_number}</p>
                      <p className="text-sm text-slate dark:text-sand/60">
                        {formatMoney(inv.total_paise)}
                        {inv.tax_paise ? ` · tax ${formatMoney(inv.tax_paise)}` : ""}
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
                      </>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {tab === "sessions" && (
        <div className="space-y-3">
          {cancellable.length > 0 && (
            <div className="rounded-2xl border border-dashed border-forest/20 p-3 dark:border-sand/20">
              <p className="mb-2 text-sm font-semibold">Cancel upcoming</p>
              <ul className="space-y-2">
                {cancellable.slice(0, 8).map((s) => (
                  <li key={s.id} className="flex items-center justify-between gap-2 text-sm">
                    <span>
                      {new Date(s.starts_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </span>
                    <Button
                      variant="ghost"
                      disabled={cancelSession.isPending}
                      onClick={() => cancelSession.mutate({ id: s.id })}
                    >
                      Cancel
                    </Button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <ul className="space-y-2">
            {(history.data ?? []).map((s) => (
              <li key={s.id}>
                <Link
                  to={`/app/sessions/${s.id}`}
                  className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
                >
                  <span>
                    {new Date(s.starts_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </span>
                  <Badge>{s.status}</Badge>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === "assessments" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Weight (kg)</Label>
              <Input
                type="number"
                value={weight}
                onChange={(e) => setWeight(Number(e.target.value))}
              />
            </div>
            <div>
              <Label>Height (cm)</Label>
              <Input
                type="number"
                value={height}
                onChange={(e) => setHeight(Number(e.target.value))}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="photo">Transformation photo</Label>
            <Input
              id="photo"
              type="file"
              accept="image/*"
              onChange={(e) => setPhotoFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <Button disabled={addAssessment.isPending} onClick={() => addAssessment.mutate()}>
            Log assessment
          </Button>
          <ul className="space-y-2">
            {(assessments.data ?? []).map((a) => (
              <li
                key={a.id}
                className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
              >
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
                        alt="Progress"
                        className="h-20 w-20 rounded-xl object-cover"
                      />
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === "notes" && (
        <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
          <p>
            <span className="font-semibold">Health history</span>
            <br />
            {c.health_history || "—"}
          </p>
          <p>
            <span className="font-semibold">Medical notes</span>
            <br />
            {c.medical_notes || "—"}
          </p>
          <p>
            <span className="font-semibold">Notes</span>
            <br />
            {c.notes || "—"}
          </p>
        </div>
      )}
    </section>
  );
}

function SummaryTile({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-3 ${
        accent
          ? "border-moss/30 bg-moss/10 dark:border-lime/30 dark:bg-lime/10"
          : "border-forest/10 bg-white/70 dark:border-sand/10 dark:bg-white/5"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
        {label}
      </p>
      <p className="mt-1 font-display text-lg font-bold text-forest dark:text-lime">{value}</p>
      <p className="mt-0.5 text-[11px] text-slate dark:text-sand/60">{hint}</p>
    </div>
  );
}
