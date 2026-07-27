import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch, type UserMe } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

const schema = z.object({
  name: z.string().min(2),
  slug: z
    .string()
    .min(2)
    .regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, and hyphens only"),
  timezone: z.string().min(1),
});

type FormValues = z.infer<typeof schema>;

export function OnboardingPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      slug: "",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    },
  });

  const mutation = useMutation({
    mutationFn: (body: FormValues) =>
      apiFetch<UserMe>("/api/v1/organizations", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => {
      void qc.setQueryData(["me"], data);
      void navigate("/app", { replace: true });
    },
  });

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center bg-fog px-5 dark:bg-ink">
      <p className="font-display text-4xl font-extrabold text-forest dark:text-lime">TetherFit</p>
      <h1 className="mt-3 font-display text-2xl font-bold">Set up your business</h1>
      <p className="mt-2 text-slate dark:text-sand/70">
        Create your organization to unlock clients, calendar, and sessions.
      </p>

      <form
        className="mt-8 space-y-4"
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
      >
        <div>
          <Label htmlFor="name">Business name</Label>
          <Input id="name" {...form.register("name")} placeholder="Peak Performance PT" />
        </div>
        <div>
          <Label htmlFor="slug">URL slug</Label>
          <Input id="slug" {...form.register("slug")} placeholder="peak-pt" />
        </div>
        <div>
          <Label htmlFor="timezone">Timezone</Label>
          <Input id="timezone" {...form.register("timezone")} />
        </div>
        {mutation.isError && (
          <p className="text-sm text-red-700 dark:text-red-300">
            Could not create organization. Check the slug is unique and try again.
          </p>
        )}
        <Button type="submit" className="w-full" disabled={mutation.isPending}>
          {mutation.isPending ? "Creating…" : "Continue"}
        </Button>
      </form>
    </div>
  );
}
