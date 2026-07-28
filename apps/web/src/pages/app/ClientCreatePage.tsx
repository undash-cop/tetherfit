import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input, Label, Textarea } from "@/components/ui/field";
import { useCreateClient } from "@/hooks/useClients";

const schema = z.object({
  full_name: z.string().min(1),
  email: z.string().email().optional().or(z.literal("")),
  phone: z.string().optional(),
  goals: z.string().optional(),
  notes: z.string().optional(),
  pt_start_at: z.string().optional(),
  pt_end_at: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function ClientCreatePage() {
  const navigate = useNavigate();
  const create = useCreateClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      goals: "",
      notes: "",
      pt_start_at: "",
      pt_end_at: "",
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">New client</h1>
      <form
        className="space-y-4"
        onSubmit={form.handleSubmit(async (values) => {
          const client = await create.mutateAsync({
            full_name: values.full_name,
            email: values.email || null,
            phone: values.phone || null,
            goals: values.goals || null,
            notes: values.notes || null,
            pt_start_at: values.pt_start_at
              ? new Date(values.pt_start_at).toISOString()
              : null,
            pt_end_at: values.pt_end_at ? new Date(values.pt_end_at).toISOString() : null,
          });
          void navigate(`/app/clients/${client.id}`);
        })}
      >
        <div>
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" {...form.register("full_name")} />
        </div>
        <div>
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" {...form.register("phone")} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...form.register("email")} />
        </div>
        <div>
          <Label htmlFor="pt_start_at">PT start</Label>
          <Input id="pt_start_at" type="date" {...form.register("pt_start_at")} />
        </div>
        <div>
          <Label htmlFor="pt_end_at">PT end</Label>
          <Input id="pt_end_at" type="date" {...form.register("pt_end_at")} />
        </div>
        <div>
          <Label htmlFor="goals">Goals</Label>
          <Textarea id="goals" {...form.register("goals")} />
        </div>
        <div>
          <Label htmlFor="notes">Notes</Label>
          <Textarea id="notes" {...form.register("notes")} />
        </div>
        <Button type="submit" className="w-full" disabled={create.isPending}>
          {create.isPending ? "Saving…" : "Save client"}
        </Button>
      </form>
    </section>
  );
}
