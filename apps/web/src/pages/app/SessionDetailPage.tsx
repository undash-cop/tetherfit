import { useState } from "react";
import { Link, useParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Textarea } from "@/components/ui/field";
import {
  useCancelSession,
  useCheckInSession,
  useFinishSession,
  useNoShowSession,
  usePauseSession,
  useResumeSession,
  useSession,
  useStartSession,
} from "@/hooks/useSessions";

async function readGeo(): Promise<{
  latitude?: number;
  longitude?: number;
  accuracy_m?: number;
}> {
  if (!navigator.geolocation) return {};
  try {
    const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 8000,
        maximumAge: 30_000,
      });
    });
    return {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
      accuracy_m: pos.coords.accuracy,
    };
  } catch {
    return {};
  }
}

export function SessionDetailPage() {
  const { id } = useParams();
  const session = useSession(id);
  const checkIn = useCheckInSession();
  const start = useStartSession();
  const pause = usePauseSession();
  const resume = useResumeSession();
  const finish = useFinishSession();
  const cancel = useCancelSession();
  const noShow = useNoShowSession();
  const [notes, setNotes] = useState("");
  const [rating, setRating] = useState(5);
  const [geoError, setGeoError] = useState<string | null>(null);

  if (session.isLoading) return <p>Loading…</p>;
  if (!session.data) return <p>Session not found.</p>;

  const s = session.data;
  const closed =
    s.status === "completed" || s.status === "cancelled" || s.status === "no_show";
  const canFinish =
    s.status === "scheduled" ||
    s.status === "checked_in" ||
    s.status === "in_progress" ||
    s.status === "paused";

  return (
    <section className="space-y-4">
      <Link to="/app/calendar" className="text-sm font-semibold text-moss dark:text-lime">
        ← Calendar
      </Link>
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">
        {s.client_name ?? "Session"}
      </h1>
      <Badge>{s.status.replace("_", " ")}</Badge>
      <div className="rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <p>
          {new Date(s.starts_at).toLocaleString()} –{" "}
          {new Date(s.ends_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
        </p>
        <p className="mt-2 text-sm text-slate dark:text-sand/60">{s.location || "No location"}</p>
        <p className="mt-2 text-sm">{s.notes || "No notes yet"}</p>
        {s.start_latitude != null && s.start_longitude != null && (
          <p className="mt-2 text-xs text-moss dark:text-lime">
            Started at {s.start_latitude.toFixed(5)}, {s.start_longitude.toFixed(5)}
            {s.start_accuracy_m != null ? ` (±${Math.round(s.start_accuracy_m)}m)` : ""}
          </p>
        )}
        {s.credit_deducted && (
          <p className="mt-2 text-xs font-semibold text-moss dark:text-lime">Credit deducted</p>
        )}
      </div>

      {!closed && (
        <div className="space-y-2">
          {s.status === "scheduled" && (
            <Button
              className="w-full"
              disabled={checkIn.isPending}
              onClick={() => checkIn.mutate({ id: s.id })}
            >
              Check in
            </Button>
          )}
          {(s.status === "scheduled" || s.status === "checked_in") && (
            <>
              <Button
                className="w-full"
                variant="secondary"
                disabled={start.isPending}
                onClick={() => {
                  void (async () => {
                    setGeoError(null);
                    const geo = await readGeo();
                    if (geo.latitude == null) {
                      setGeoError("Location unavailable — starting without GPS.");
                    }
                    start.mutate({ id: s.id, body: geo });
                  })();
                }}
              >
                Start session
              </Button>
              {geoError && <p className="text-xs text-amber-700 dark:text-amber-300">{geoError}</p>}
            </>
          )}
          {s.status === "in_progress" && (
            <Button
              className="w-full"
              variant="outline"
              disabled={pause.isPending}
              onClick={() => pause.mutate({ id: s.id })}
            >
              Pause
            </Button>
          )}
          {s.status === "paused" && (
            <Button
              className="w-full"
              variant="secondary"
              disabled={resume.isPending}
              onClick={() => resume.mutate({ id: s.id })}
            >
              Resume
            </Button>
          )}
          {canFinish && (
            <>
              <Textarea
                placeholder="Session notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold">Rating</p>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setRating(n)}
                    className={`min-h-10 min-w-10 rounded-xl text-sm font-bold ${
                      rating === n
                        ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                        : "bg-white/70 dark:bg-white/5"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <Button
                className="w-full"
                disabled={finish.isPending}
                onClick={() =>
                  finish.mutate({
                    id: s.id,
                    body: { notes: notes || undefined, rating },
                  })
                }
              >
                Finish session
              </Button>
              {(s.status === "scheduled" || s.status === "checked_in") && (
                <Button
                  className="w-full"
                  variant="outline"
                  disabled={noShow.isPending}
                  onClick={() => noShow.mutate({ id: s.id })}
                >
                  Mark no-show
                </Button>
              )}
              <Button
                className="w-full"
                variant="ghost"
                disabled={cancel.isPending}
                onClick={() => cancel.mutate({ id: s.id })}
              >
                Cancel
              </Button>
            </>
          )}
        </div>
      )}
    </section>
  );
}
