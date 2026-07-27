import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { useMe } from "@/hooks/useMe";
import { apiFetch } from "@/lib/api";
import { getToken, logout } from "@/lib/auth/keycloak";

export function ClientProfilePage() {
  const me = useMe();
  const [goals, setGoals] = useState("");
  const [phone, setPhone] = useState("");
  const [invite, setInvite] = useState("");

  const save = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/portal/profile", {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify({ goals: goals || undefined, phone: phone || undefined }),
      }),
  });

  const accept = useMutation({
    mutationFn: () =>
      apiFetch(`/api/v1/portal/accept-invite/${invite.trim()}`, {
        method: "POST",
        token: getToken(),
      }),
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Profile</h1>
      <div className="rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
        <p className="font-semibold">{me.data?.full_name}</p>
        <p className="text-sm text-slate dark:text-sand/60">{me.data?.email}</p>
      </div>
      <div className="space-y-2">
        <Label>Goals</Label>
        <Input value={goals} onChange={(e) => setGoals(e.target.value)} />
        <Label>Phone</Label>
        <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
        <Button onClick={() => save.mutate()}>Save</Button>
      </div>
      <div className="space-y-2 rounded-2xl border border-dashed border-forest/20 p-4 dark:border-sand/20">
        <Label>Accept portal invite token</Label>
        <Input value={invite} onChange={(e) => setInvite(e.target.value)} />
        <Button variant="secondary" disabled={!invite} onClick={() => accept.mutate()}>
          Link coach
        </Button>
        {accept.isSuccess && <p className="text-sm text-moss">Linked successfully.</p>}
      </div>
      <Button variant="outline" className="w-full" onClick={() => void logout()}>
        Log out
      </Button>
    </section>
  );
}
