import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";
import { useCalendar, useCreateSession, useRescheduleSession } from "@/hooks/useSessions";
import type { PtSession } from "@/lib/api";

type View = "day" | "week" | "month";

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

function addDays(d: Date, n: number) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

function formatDay(d: Date) {
  return d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
}

const HOURS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];

export function CalendarPage() {
  const [params, setParams] = useSearchParams();
  const [view, setView] = useState<View>("week");
  const [anchor, setAnchor] = useState(() => startOfDay(new Date()));
  const bookOpen = params.get("book") === "1";
  const presetClient = params.get("client") || "";
  const [dragId, setDragId] = useState<string | null>(null);

  const range = useMemo(() => {
    if (view === "day") {
      return { from: anchor, to: addDays(anchor, 1) };
    }
    if (view === "week") {
      const day = anchor.getDay();
      const mondayOffset = day === 0 ? -6 : 1 - day;
      const start = addDays(anchor, mondayOffset);
      return { from: start, to: addDays(start, 7) };
    }
    const start = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
    const end = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 1);
    return { from: startOfDay(start), to: startOfDay(end) };
  }, [anchor, view]);

  const { data: sessions, isLoading } = useCalendar(
    range.from.toISOString(),
    range.to.toISOString(),
  );
  const clients = useClients();
  const create = useCreateSession();
  const reschedule = useRescheduleSession();

  const [clientId, setClientId] = useState(presetClient);
  const [startsLocal, setStartsLocal] = useState("");
  const [duration, setDuration] = useState(60);

  const byDay = useMemo(() => {
    const map = new Map<string, PtSession[]>();
    for (const s of sessions ?? []) {
      const key = startOfDay(new Date(s.starts_at)).toISOString();
      const list = map.get(key) ?? [];
      list.push(s);
      map.set(key, list);
    }
    return map;
  }, [sessions]);

  const days: Date[] = [];
  for (let d = new Date(range.from); d < range.to; d = addDays(d, 1)) {
    days.push(new Date(d));
  }

  function onDropSlot(day: Date, hour: number) {
    if (!dragId) return;
    const session = (sessions ?? []).find((s) => s.id === dragId);
    if (!session) return;
    const durationMs =
      new Date(session.ends_at).getTime() - new Date(session.starts_at).getTime();
    const starts = new Date(day);
    starts.setHours(hour, 0, 0, 0);
    const ends = new Date(starts.getTime() + Math.max(durationMs, 30 * 60_000));
    reschedule.mutate({
      id: dragId,
      starts_at: starts.toISOString(),
      ends_at: ends.toISOString(),
    });
    setDragId(null);
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Calendar</h1>
        <Button
          variant="secondary"
          onClick={() => {
            params.set("book", "1");
            setParams(params);
          }}
        >
          Book
        </Button>
      </div>
      {(view === "day" || view === "week") && (
        <p className="text-xs text-slate dark:text-sand/60">
          Drag a session onto a time slot to reschedule.
        </p>
      )}

      <div className="flex gap-2">
        {(["day", "week", "month"] as View[]).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setView(v)}
            className={`min-h-10 rounded-xl px-3 text-sm font-semibold capitalize ${
              view === v
                ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                : "bg-white/70 dark:bg-white/5"
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() =>
            setAnchor(addDays(anchor, view === "month" ? -30 : view === "week" ? -7 : -1))
          }
        >
          Prev
        </Button>
        <p className="text-sm font-medium">{formatDay(range.from)}</p>
        <Button
          variant="ghost"
          onClick={() =>
            setAnchor(addDays(anchor, view === "month" ? 30 : view === "week" ? 7 : 1))
          }
        >
          Next
        </Button>
      </div>

      {isLoading && <p className="text-sm text-slate">Loading…</p>}

      {(view === "day" || view === "week") && (
        <div className="space-y-4">
          {days.map((day) => {
            const key = startOfDay(day).toISOString();
            const items = byDay.get(key) ?? [];
            return (
              <div key={key}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
                  {formatDay(day)}
                </p>
                <ul className="mb-2 space-y-2">
                  {items.map((s) => (
                    <li key={s.id}>
                      <div
                        draggable
                        onDragStart={() => setDragId(s.id)}
                        onDragEnd={() => setDragId(null)}
                        className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-3 py-3 dark:border-sand/10 dark:bg-white/5"
                      >
                        <Link to={`/app/sessions/${s.id}`} className="min-w-0 flex-1">
                          <p className="font-semibold">{s.client_name}</p>
                          <p className="text-xs text-slate dark:text-sand/60">
                            {new Date(s.starts_at).toLocaleTimeString([], {
                              hour: "numeric",
                              minute: "2-digit",
                            })}{" "}
                            · {s.status.replace("_", " ")}
                          </p>
                        </Link>
                        <span className="text-[10px] font-semibold uppercase text-slate/70">
                          Drag
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="grid grid-cols-4 gap-1 sm:grid-cols-7">
                  {HOURS.map((hour) => (
                    <button
                      key={`${key}-${hour}`}
                      type="button"
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={() => onDropSlot(day, hour)}
                      className="min-h-10 rounded-lg border border-dashed border-forest/15 text-[10px] text-slate dark:border-sand/15 dark:text-sand/50"
                    >
                      {hour}:00
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {view === "month" && (
        <div className="space-y-4">
          {days.map((day) => {
            const key = startOfDay(day).toISOString();
            const items = byDay.get(key) ?? [];
            if (items.length === 0) return null;
            return (
              <div key={key}>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
                  {formatDay(day)}
                </p>
                <ul className="space-y-2">
                  {items.map((s) => (
                    <li key={s.id}>
                      <Link
                        to={`/app/sessions/${s.id}`}
                        className="flex justify-between rounded-2xl border border-forest/10 bg-white/70 px-3 py-3 dark:border-sand/10 dark:bg-white/5"
                      >
                        <div>
                          <p className="font-semibold">{s.client_name}</p>
                          <p className="text-xs text-slate dark:text-sand/60">
                            {new Date(s.starts_at).toLocaleTimeString([], {
                              hour: "numeric",
                              minute: "2-digit",
                            })}{" "}
                            · {s.status.replace("_", " ")}
                          </p>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}

      {bookOpen && (
        <div className="fixed inset-0 z-40 flex items-end bg-ink/50 p-4 sm:items-center sm:justify-center">
          <form
            className="w-full max-w-md space-y-3 rounded-3xl bg-fog p-5 dark:bg-forest"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!clientId || !startsLocal) return;
              const starts = new Date(startsLocal);
              const ends = new Date(starts.getTime() + duration * 60_000);
              const session = await create.mutateAsync({
                client_id: clientId,
                starts_at: starts.toISOString(),
                ends_at: ends.toISOString(),
              });
              params.delete("book");
              setParams(params);
              window.location.assign(`/app/sessions/${session.id}`);
            }}
          >
            <h2 className="font-display text-2xl font-bold">Book session</h2>
            <div>
              <Label htmlFor="client">Client</Label>
              <select
                id="client"
                className="min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm dark:border-sand/15 dark:bg-white/5"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                required
              >
                <option value="">Select…</option>
                {(clients.data?.items ?? []).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="starts">Starts</Label>
              <Input
                id="starts"
                type="datetime-local"
                value={startsLocal}
                onChange={(e) => setStartsLocal(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="duration">Duration (min)</Label>
              <Input
                id="duration"
                type="number"
                min={15}
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
              />
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                className="flex-1"
                onClick={() => {
                  params.delete("book");
                  setParams(params);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" className="flex-1" disabled={create.isPending}>
                Save
              </Button>
            </div>
          </form>
        </div>
      )}
    </section>
  );
}
