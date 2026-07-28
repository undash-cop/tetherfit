import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Badge, Input, Label } from "@/components/ui/field";
import { useClient, useClientPackages, useCreatePackage } from "@/hooks/useClients";
import { useClientSessions } from "@/hooks/useSessions";
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

export function ClientDetailPage() {
  const { id } = useParams();
  const client = useClient(id);
  const packages = useClientPackages(id);
  const history = useClientSessions(id);
  const createPkg = useCreatePackage(id!);
  const qc = useQueryClient();
  const [sessions, setSessions] = useState(10);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [weight, setWeight] = useState(70);
  const [height, setHeight] = useState(170);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [tab, setTab] = useState<
    "overview" | "credits" | "sessions" | "assessments" | "notes"
  >("overview");

  const assessments = useQuery({
    queryKey: ["assessments", id],
    queryFn: () =>
      apiFetch<Assessment[]>(`/api/v1/assessments?client_id=${id}`, { token: getToken() }),
    enabled: Boolean(id),
  });

  const invitePortal = useMutation({
    mutationFn: () =>
      apiFetch<{ token: string }>(`/api/v1/clients/${id}/portal-invite`, {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({}),
      }),
    onSuccess: (data) => setInviteToken(data.token),
  });

  const openChat = useMutation({
    mutationFn: () =>
      apiFetch<{ id: string }>(`/api/v1/chat/threads/${id}`, {
        method: "POST",
        token: getToken(),
      }),
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
        photoUrls.push(
          presign.public_url || `https://media.local/${presign.object_key}`,
        );
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

  return (
    <section className="space-y-4">
      <div>
        <Link to="/app/clients" className="text-sm font-semibold text-moss dark:text-lime">
          ← Clients
        </Link>
        <h1 className="mt-2 font-display text-3xl font-bold text-forest dark:text-lime">
          {c.full_name}
        </h1>
        <div className="mt-2 flex gap-2">
          <Badge>{c.status}</Badge>
          <Badge className="bg-moss/15 text-moss dark:bg-lime/15 dark:text-lime">
            {c.remaining_credits ?? 0} credits
          </Badge>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {(["overview", "credits", "sessions", "assessments", "notes"] as const).map((t) => (
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
        <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
          <p>
            <span className="text-slate dark:text-sand/60">Phone:</span> {c.phone || "—"}
          </p>
          <p>
            <span className="text-slate dark:text-sand/60">Email:</span> {c.email || "—"}
          </p>
          <p>
            <span className="text-slate dark:text-sand/60">Goals:</span> {c.goals || "—"}
          </p>
          <Link to={`/app/calendar?book=1&client=${c.id}`}>
            <Button className="mt-2 w-full">Book session</Button>
          </Link>
          <Button
            className="w-full"
            variant="secondary"
            disabled={invitePortal.isPending}
            onClick={() => invitePortal.mutate()}
          >
            Invite to client portal
          </Button>
          {inviteToken && (
            <p className="break-all rounded-xl bg-sand/50 p-2 text-xs dark:bg-white/10">
              Invite token: {inviteToken}
            </p>
          )}
          <Button className="w-full" variant="outline" onClick={() => openChat.mutate()}>
            Open chat thread
          </Button>
          <Link to="/app/chat">
            <Button className="w-full" variant="ghost">
              Go to chat
            </Button>
          </Link>
        </div>
      )}

      {tab === "credits" && (
        <div className="space-y-4">
          <ul className="space-y-2">
            {(packages.data ?? []).map((p) => (
              <li
                key={p.id}
                className="rounded-2xl border border-forest/10 bg-white/70 px-4 py-3 dark:border-sand/10 dark:bg-white/5"
              >
                <p className="font-semibold">
                  {p.remaining_sessions} / {p.total_sessions} remaining
                </p>
              </li>
            ))}
          </ul>
          <div className="rounded-2xl border border-dashed border-forest/20 p-4 dark:border-sand/20">
            <Label htmlFor="pack">Grant package (sessions)</Label>
            <Input
              id="pack"
              type="number"
              min={1}
              value={sessions}
              onChange={(e) => setSessions(Number(e.target.value))}
            />
            <Button
              className="mt-3 w-full"
              disabled={createPkg.isPending}
              onClick={() => createPkg.mutate({ total_sessions: sessions, notes: "Manual pack" })}
            >
              Add credits
            </Button>
          </div>
        </div>
      )}

      {tab === "sessions" && (
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
