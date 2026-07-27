import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { Input, Label, Textarea } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";
import { useClients } from "@/hooks/useClients";

type Exercise = { id: string; name: string; muscle_group: string | null };
type WorkoutPlan = {
  id: string;
  name: string;
  description: string | null;
  items: { name: string; sets: number; reps: string }[];
};
type Assignment = {
  id: string;
  client_id: string;
  workout_plan_id: string;
  plan_name: string | null;
  assigned_at: string;
};

export function WorkoutsPage() {
  const qc = useQueryClient();
  const clients = useClients();
  const exercises = useQuery({
    queryKey: ["exercises"],
    queryFn: () => apiFetch<Exercise[]>("/api/v1/exercises", { token: getToken() }),
  });
  const plans = useQuery({
    queryKey: ["workouts"],
    queryFn: () => apiFetch<WorkoutPlan[]>("/api/v1/workouts", { token: getToken() }),
  });
  const assignments = useQuery({
    queryKey: ["workout-assignments"],
    queryFn: () =>
      apiFetch<Assignment[]>("/api/v1/workout-assignments", { token: getToken() }),
  });

  const [exName, setExName] = useState("");
  const [planName, setPlanName] = useState("");
  const [planItems, setPlanItems] = useState("Squat,3,8\nBench Press,3,10");
  const [assignClient, setAssignClient] = useState("");
  const [assignPlan, setAssignPlan] = useState("");

  const createEx = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/exercises", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ name: exName }),
      }),
    onSuccess: () => {
      setExName("");
      void qc.invalidateQueries({ queryKey: ["exercises"] });
    },
  });

  const createPlan = useMutation({
    mutationFn: () => {
      const items = planItems
        .split("\n")
        .map((line, order) => {
          const [name, sets, reps] = line.split(",").map((s) => s.trim());
          return { name, sets: Number(sets || 3), reps: reps || "10", order };
        })
        .filter((i) => i.name);
      return apiFetch("/api/v1/workouts", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ name: planName, items }),
      });
    },
    onSuccess: () => {
      setPlanName("");
      void qc.invalidateQueries({ queryKey: ["workouts"] });
    },
  });

  const assign = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/workout-assignments", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({ client_id: assignClient, workout_plan_id: assignPlan }),
      }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["workout-assignments"] }),
  });

  return (
    <section className="space-y-6">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Workouts</h1>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Exercise library</h2>
        <div className="flex gap-2">
          <Input
            placeholder="Exercise name"
            value={exName}
            onChange={(e) => setExName(e.target.value)}
          />
          <Button disabled={!exName || createEx.isPending} onClick={() => createEx.mutate()}>
            Add
          </Button>
        </div>
        <ul className="space-y-1 text-sm">
          {(exercises.data ?? []).slice(0, 8).map((e) => (
            <li key={e.id}>{e.name}</li>
          ))}
        </ul>
      </div>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Plans</h2>
        <Label>Name</Label>
        <Input value={planName} onChange={(e) => setPlanName(e.target.value)} />
        <Label>Items (name,sets,reps per line)</Label>
        <Textarea value={planItems} onChange={(e) => setPlanItems(e.target.value)} />
        <Button disabled={!planName || createPlan.isPending} onClick={() => createPlan.mutate()}>
          Save plan
        </Button>
        <ul className="mt-3 space-y-2">
          {(plans.data ?? []).map((p) => (
            <li key={p.id} className="rounded-xl bg-sand/50 px-3 py-2 dark:bg-white/5">
              <p className="font-semibold">{p.name}</p>
              <p className="text-xs text-slate dark:text-sand/60">{p.items.length} exercises</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-3 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <h2 className="font-display text-xl font-bold">Assign to client</h2>
        <select
          className="min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm dark:bg-white/5"
          value={assignClient}
          onChange={(e) => setAssignClient(e.target.value)}
        >
          <option value="">Client…</option>
          {(clients.data?.items ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name}
            </option>
          ))}
        </select>
        <select
          className="min-h-11 w-full rounded-xl border border-forest/15 bg-white px-3 text-sm dark:bg-white/5"
          value={assignPlan}
          onChange={(e) => setAssignPlan(e.target.value)}
        >
          <option value="">Plan…</option>
          {(plans.data ?? []).map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <Button
          disabled={!assignClient || !assignPlan || assign.isPending}
          onClick={() => assign.mutate()}
        >
          Assign
        </Button>
        <ul className="space-y-2 text-sm">
          {(assignments.data ?? []).slice(0, 5).map((a) => (
            <li key={a.id}>
              <Link to={`/app/clients/${a.client_id}`} className="font-medium text-moss dark:text-lime">
                {a.plan_name}
              </Link>{" "}
              · {new Date(a.assigned_at).toLocaleDateString()}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
