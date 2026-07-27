import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label, Textarea } from "@/components/ui/field";
import { useClients } from "@/hooks/useClients";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type MealPlan = {
  id: string;
  name: string;
  calories: number | null;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  client_id: string | null;
};

export function NutritionPage() {
  const clients = useClients();
  const qc = useQueryClient();
  const plans = useQuery({
    queryKey: ["meal-plans"],
    queryFn: () => apiFetch<MealPlan[]>("/api/v1/meal-plans", { token: getToken() }),
  });
  const [name, setName] = useState("");
  const [clientId, setClientId] = useState("");
  const [calories, setCalories] = useState(2000);
  const [protein, setProtein] = useState(150);
  const [notes, setNotes] = useState("");

  const create = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/meal-plans", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          name,
          client_id: clientId || null,
          calories,
          protein_g: protein,
          carbs_g: 200,
          fat_g: 60,
          meals: [{ name: "Breakfast", items: ["Oats", "Eggs"] }],
          notes,
        }),
      }),
    onSuccess: () => {
      setName("");
      void qc.invalidateQueries({ queryKey: ["meal-plans"] });
    },
  });

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Nutrition</h1>
      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <Label>Plan name</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
        <Label>Client (optional)</Label>
        <select
          className="min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm dark:bg-white/5"
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
        >
          <option value="">Template</option>
          {(clients.data?.items ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name}
            </option>
          ))}
        </select>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <Label>Calories</Label>
            <Input
              type="number"
              value={calories}
              onChange={(e) => setCalories(Number(e.target.value))}
            />
          </div>
          <div>
            <Label>Protein (g)</Label>
            <Input
              type="number"
              value={protein}
              onChange={(e) => setProtein(Number(e.target.value))}
            />
          </div>
        </div>
        <Label>Notes</Label>
        <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
        <Button disabled={!name || create.isPending} onClick={() => create.mutate()}>
          Save meal plan
        </Button>
      </div>
      <ul className="space-y-2">
        {(plans.data ?? []).map((p) => (
          <li
            key={p.id}
            className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10"
          >
            <p className="font-semibold">{p.name}</p>
            <p className="text-sm text-slate dark:text-sand/60">
              {p.calories ?? "—"} kcal · P {p.protein_g ?? "—"}g
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
