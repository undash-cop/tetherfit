import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Rule = {
  id: string;
  client_id: string;
  frequency: string;
  byweekday: number[];
  starts_on: string;
  sessions_created?: number;
  active: boolean;
};

type Slot = { id: string; weekday: number; start_minute: number; end_minute: number };

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function SchedulingPage() {
  const qc = useQueryClient();
  const clients = useClients("");
  const [clientId, setClientId] = useState("");
  const [starts, setStarts] = useState("");
  const [weekdays, setWeekdays] = useState<number[]>([0]);

  const rules = useQuery({
    queryKey: ["recurrence-rules"],
    queryFn: () => apiFetch<Rule[]>("/api/v1/recurrence-rules", { token: getToken() }),
  });
  const availability = useQuery({
    queryKey: ["availability"],
    queryFn: () => apiFetch<Slot[]>("/api/v1/availability", { token: getToken() }),
  });

  const createRule = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/recurrence-rules", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          client_id: clientId,
          frequency: "weekly",
          byweekday: [...weekdays].sort((a, b) => a - b),
          starts_on: new Date(starts).toISOString(),
          duration_minutes: 60,
          generate_weeks: 8,
        }),
      }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["recurrence-rules"] });
      void qc.invalidateQueries({ queryKey: ["calendar"] });
    },
  });

  function toggleWeekday(day: number) {
    setWeekdays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    );
  }

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
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Scheduling</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Recurring sessions and weekly availability.
        </p>
      </div>

      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <h2 className="font-display text-xl font-bold">New weekly series</h2>
        <Label>Client</Label>
        <select
          className="min-h-11 w-full rounded-xl border border-forest/15 bg-white/80 px-3 dark:border-sand/15 dark:bg-white/5"
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
        <Label>First session</Label>
        <Input type="datetime-local" value={starts} onChange={(e) => setStarts(e.target.value)} />
        <Label>Weekdays</Label>
        <div className="flex flex-wrap gap-2">
          {days.map((d, i) => {
            const selected = weekdays.includes(i);
            return (
              <button
                key={d}
                type="button"
                aria-pressed={selected}
                onClick={() => toggleWeekday(i)}
                className={`min-h-10 rounded-xl px-3 text-sm font-semibold ${
                  selected
                    ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                    : "bg-white/70 dark:bg-white/5"
                }`}
              >
                {d}
              </button>
            );
          })}
        </div>
        <Button
          disabled={!clientId || !starts || weekdays.length === 0 || createRule.isPending}
          onClick={() => createRule.mutate()}
        >
          Generate 8 weeks
        </Button>
      </div>

      <ul className="space-y-2">
        {(rules.data ?? []).map((r) => (
          <li key={r.id} className="rounded-xl border border-forest/10 px-3 py-2 text-sm dark:border-sand/10">
            {r.frequency} ·{" "}
            {(r.byweekday ?? []).map((d) => days[d] ?? d).join(", ") || "—"} ·{" "}
            {r.active ? "active" : "off"}
            {r.sessions_created != null ? ` · +${r.sessions_created}` : ""}
          </li>
        ))}
      </ul>

      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <h2 className="font-display text-xl font-bold">Availability</h2>
        <Button variant="secondary" onClick={() => saveAvailability.mutate()}>
          Set Mon–Fri 9–17
        </Button>
        <ul className="text-sm">
          {(availability.data ?? []).map((s) => (
            <li key={s.id}>
              {days[s.weekday]} {Math.floor(s.start_minute / 60)}:00–
              {Math.floor(s.end_minute / 60)}:00
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
