import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input, Label, Textarea } from "@/components/ui/field";
import { useMe } from "@/hooks/useMe";
import { apiFetch, type UserMe } from "@/lib/api";
import { getToken, logout } from "@/lib/auth/keycloak";

const schema = z.object({
  name: z.string().min(2),
  timezone: z.string().min(1),
  gstin: z.string().optional(),
  business_address: z.string().optional(),
  business_phone: z.string().optional(),
  upi_vpa: z.string().optional(),
  default_gst_pct: z.coerce.number().min(0).max(100),
});

type FormValues = z.infer<typeof schema>;

type Slot = { id: string; weekday: number; start_minute: number; end_minute: number };

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function SettingsPage() {
  const me = useMe();
  const qc = useQueryClient();
  const org = me.data?.organization;
  const form = useForm<FormValues>({
    values: {
      name: org?.name ?? "",
      timezone: org?.timezone ?? "UTC",
      gstin: org?.gstin ?? "",
      business_address: org?.business_address ?? "",
      business_phone: org?.business_phone ?? "",
      upi_vpa: org?.upi_vpa ?? "",
      default_gst_pct: org?.default_gst_pct ?? 0,
    },
    resolver: zodResolver(schema),
  });

  const availability = useQuery({
    queryKey: ["availability"],
    queryFn: () => apiFetch<Slot[]>("/api/v1/availability", { token: getToken() }),
  });

  const mutation = useMutation({
    mutationFn: (body: FormValues) =>
      apiFetch("/api/v1/organizations/me", {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify({
          name: body.name,
          timezone: body.timezone,
          gstin: body.gstin || null,
          business_address: body.business_address || null,
          business_phone: body.business_phone || null,
          upi_vpa: body.upi_vpa || null,
          default_gst_pct: body.default_gst_pct,
        }),
      }),
    onSuccess: async () => {
      const updated = await apiFetch<UserMe>("/api/v1/me", { token: getToken() });
      void qc.setQueryData(["me"], updated);
    },
  });

  const saveAvailability = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/availability", {
        method: "PUT",
        token: getToken(),
        body: JSON.stringify([
          { weekday: 0, start_minute: 9 * 60, end_minute: 17 * 60 },
          { weekday: 1, start_minute: 9 * 60, end_minute: 17 * 60 },
          { weekday: 2, start_minute: 9 * 60, end_minute: 17 * 60 },
          { weekday: 3, start_minute: 9 * 60, end_minute: 17 * 60 },
          { weekday: 4, start_minute: 9 * 60, end_minute: 17 * 60 },
        ]),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["availability"] }),
  });

  return (
    <section className="space-y-6">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Settings</h1>

      <div className="rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Trainer profile</h2>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          {me.data?.full_name || "—"} · {me.data?.email || "No email"}
        </p>
        <p className="text-xs text-slate dark:text-sand/60">Role: {me.data?.org_role}</p>
      </div>

      <form
        className="space-y-4 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <h2 className="font-display text-xl font-bold">Business & GST</h2>
        <div>
          <Label htmlFor="name">Business name</Label>
          <Input id="name" {...form.register("name")} />
        </div>
        <div>
          <Label htmlFor="timezone">Timezone</Label>
          <Input id="timezone" {...form.register("timezone")} />
        </div>
        <div>
          <Label htmlFor="gstin">GSTIN</Label>
          <Input id="gstin" {...form.register("gstin")} placeholder="22AAAAA0000A1Z5" />
        </div>
        <div>
          <Label htmlFor="business_address">Business address</Label>
          <Textarea id="business_address" {...form.register("business_address")} />
        </div>
        <div>
          <Label htmlFor="business_phone">Business phone</Label>
          <Input id="business_phone" {...form.register("business_phone")} />
        </div>
        <div>
          <Label htmlFor="upi_vpa">UPI VPA (for QR payments)</Label>
          <Input id="upi_vpa" {...form.register("upi_vpa")} placeholder="trainer@upi" />
        </div>
        <div>
          <Label htmlFor="default_gst_pct">Default GST %</Label>
          <Input
            id="default_gst_pct"
            type="number"
            step="0.01"
            {...form.register("default_gst_pct")}
          />
        </div>
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          Save business settings
        </Button>
      </form>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Availability</h2>
        <Button
          variant="secondary"
          className="w-full"
          disabled={saveAvailability.isPending}
          onClick={() => saveAvailability.mutate()}
        >
          Set Mon–Fri 9–17
        </Button>
        <ul className="text-sm text-slate dark:text-sand/70">
          {(availability.data ?? []).map((s) => (
            <li key={s.id}>
              {days[s.weekday]} {Math.floor(s.start_minute / 60)}:00–
              {Math.floor(s.end_minute / 60)}:00
            </li>
          ))}
          {(availability.data ?? []).length === 0 && <li>No weekly slots yet.</li>}
        </ul>
      </div>

      <Button variant="secondary" className="w-full" onClick={() => void logout()}>
        Log out
      </Button>
    </section>
  );
}
