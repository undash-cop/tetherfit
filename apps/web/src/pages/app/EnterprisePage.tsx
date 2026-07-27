import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Member = { id: string; full_name: string; email: string | null; org_role: string };
type Invite = { id: string; email: string; org_role: string; token: string; status: string };
type Org = {
  name: string;
  plan: string;
  gstin: string | null;
  subscription_status: string;
  feature_flags: Record<string, boolean>;
};
type ApiKey = { id: string; name: string; key_prefix: string; revoked_at: string | null };

export function EnterprisePage() {
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [gstin, setGstin] = useState("");
  const [keyName, setKeyName] = useState("Default");
  const [createdKey, setCreatedKey] = useState<string | null>(null);

  const org = useQuery({
    queryKey: ["enterprise-org"],
    queryFn: () => apiFetch<Org>("/api/v1/enterprise/org", { token: getToken() }),
  });
  const team = useQuery({
    queryKey: ["enterprise-team"],
    queryFn: () => apiFetch<Member[]>("/api/v1/enterprise/team", { token: getToken() }),
  });
  const invites = useQuery({
    queryKey: ["enterprise-invites"],
    queryFn: () => apiFetch<Invite[]>("/api/v1/enterprise/team/invites", { token: getToken() }),
  });
  const keys = useQuery({
    queryKey: ["enterprise-keys"],
    queryFn: () => apiFetch<ApiKey[]>("/api/v1/enterprise/api-keys", { token: getToken() }),
  });

  const invite = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/enterprise/team/invites", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ email, org_role: "trainer" }),
      }),
    onSuccess: () => {
      setEmail("");
      void qc.invalidateQueries({ queryKey: ["enterprise-invites"] });
    },
  });

  const saveOrg = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/enterprise/org", {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify({
          gstin: gstin || org.data?.gstin,
          plan: "studio",
          feature_flags: { ...(org.data?.feature_flags ?? {}), multi_trainer: true },
        }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["enterprise-org"] }),
  });

  const createKey = useMutation({
    mutationFn: () =>
      apiFetch<{ api_key: string }>("/api/v1/enterprise/api-keys", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ name: keyName }),
      }),
    onSuccess: (data) => {
      setCreatedKey(data.api_key);
      void qc.invalidateQueries({ queryKey: ["enterprise-keys"] });
    },
  });

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Enterprise</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Team, plan, feature flags, and API keys for studio-scale ops.
        </p>
      </div>

      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <p className="font-semibold">
          {org.data?.name} · {org.data?.plan} · {org.data?.subscription_status}
        </p>
        <Label>GSTIN</Label>
        <Input
          value={gstin || org.data?.gstin || ""}
          onChange={(e) => setGstin(e.target.value)}
          placeholder="22AAAAA0000A1Z5"
        />
        <Button variant="secondary" onClick={() => saveOrg.mutate()}>
          Save studio settings
        </Button>
      </div>

      <div className="space-y-2">
        <h2 className="font-display text-xl font-bold">Team</h2>
        <ul className="space-y-2">
          {(team.data ?? []).map((m) => (
            <li key={m.id} className="rounded-xl border border-forest/10 px-3 py-2 text-sm dark:border-sand/10">
              {m.full_name || m.email} · {m.org_role}
            </li>
          ))}
        </ul>
        <Label>Invite trainer email</Label>
        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <Button disabled={!email || invite.isPending} onClick={() => invite.mutate()}>
          Send invite
        </Button>
        {(invites.data ?? []).map((i) => (
          <p key={i.id} className="text-xs text-slate dark:text-sand/60">
            Pending {i.email} · token {i.token.slice(0, 8)}…
          </p>
        ))}
      </div>

      <div className="space-y-2">
        <h2 className="font-display text-xl font-bold">API keys</h2>
        <Input value={keyName} onChange={(e) => setKeyName(e.target.value)} />
        <Button onClick={() => createKey.mutate()}>Create key</Button>
        {createdKey && (
          <p className="break-all rounded-xl bg-sand/40 p-2 text-xs dark:bg-white/10">
            Copy now: {createdKey}
          </p>
        )}
        <ul className="space-y-1 text-sm">
          {(keys.data ?? []).map((k) => (
            <li key={k.id}>
              {k.name} · {k.key_prefix}…
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
