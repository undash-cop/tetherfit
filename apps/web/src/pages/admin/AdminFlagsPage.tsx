import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Flag = { id: string; key: string; enabled: boolean; description: string | null };

export function AdminFlagsPage() {
  const qc = useQueryClient();
  const [key, setKey] = useState("marketplace_v2");
  const flags = useQuery({
    queryKey: ["admin-flags"],
    queryFn: () => apiFetch<Flag[]>("/api/v1/admin/flags", { token: getToken() }),
  });

  const upsert = useMutation({
    mutationFn: (enabled: boolean) =>
      apiFetch("/api/v1/admin/flags", {
        method: "PUT",
        token: getToken(),
        body: JSON.stringify({ key, enabled, description: "Phase 4 platform flag" }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["admin-flags"] }),
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Feature flags</h1>
      <div className="space-y-2 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <Label>Key</Label>
        <Input value={key} onChange={(e) => setKey(e.target.value)} />
        <div className="flex gap-2">
          <Button onClick={() => upsert.mutate(true)}>Enable</Button>
          <Button variant="outline" onClick={() => upsert.mutate(false)}>
            Disable
          </Button>
        </div>
      </div>
      <ul className="space-y-2">
        {(flags.data ?? []).map((f) => (
          <li
            key={f.id}
            className="rounded-xl border border-forest/10 px-3 py-2 text-sm dark:border-sand/10"
          >
            <span className="font-semibold">{f.key}</span> · {f.enabled ? "on" : "off"}
          </li>
        ))}
      </ul>
    </section>
  );
}
