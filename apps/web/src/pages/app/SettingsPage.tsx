import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { useMe } from "@/hooks/useMe";
import { apiFetch, type UserMe } from "@/lib/api";
import { getToken, logout } from "@/lib/auth/keycloak";

const schema = z.object({
  name: z.string().min(2),
  timezone: z.string().min(1),
});

type FormValues = z.infer<typeof schema>;

export function SettingsPage() {
  const me = useMe();
  const qc = useQueryClient();
  const form = useForm<FormValues>({
    values: {
      name: me.data?.organization?.name ?? "",
      timezone: me.data?.organization?.timezone ?? "UTC",
    },
    resolver: zodResolver(schema),
  });

  const mutation = useMutation({
    mutationFn: (body: FormValues) =>
      apiFetch("/api/v1/organizations/me", {
        method: "PATCH",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: async () => {
      const updated = await apiFetch<UserMe>("/api/v1/me", { token: getToken() });
      void qc.setQueryData(["me"], updated);
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Settings</h1>
      <form
        className="space-y-4"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <div>
          <Label htmlFor="name">Organization name</Label>
          <Input id="name" {...form.register("name")} />
        </div>
        <div>
          <Label htmlFor="timezone">Timezone</Label>
          <Input id="timezone" {...form.register("timezone")} />
        </div>
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          Save
        </Button>
      </form>
      <Button variant="secondary" className="w-full" onClick={() => void logout()}>
        Log out
      </Button>
    </section>
  );
}
