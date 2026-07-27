import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type AiOut = {
  feature: string;
  provider: string;
  model: string | null;
  result: Record<string, unknown>;
};

const actions = [
  {
    id: "workout",
    label: "Workout",
    path: "/api/v1/ai/workout",
    placeholder: "4-day hypertrophy for intermediate",
  },
  {
    id: "diet",
    label: "Diet",
    path: "/api/v1/ai/diet",
    placeholder: "2200 kcal high protein vegetarian",
  },
  {
    id: "session-summary",
    label: "Session summary",
    path: "/api/v1/ai/session-summary",
    placeholder: "Completed squats 3x8, good form...",
  },
  {
    id: "copilot",
    label: "Copilot",
    path: "/api/v1/ai/copilot",
    placeholder: "How should I price 12-session packs?",
  },
  {
    id: "insights",
    label: "Insights",
    path: "/api/v1/ai/insights",
    placeholder: "Focus on retention this month",
  },
] as const;

export function AiCopilotPage() {
  const [action, setAction] = useState<(typeof actions)[number]>(actions[0]);
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<AiOut | null>(null);

  const run = useMutation({
    mutationFn: async () => {
      const body =
        action.id === "copilot"
          ? { message: prompt || action.placeholder }
          : { prompt: prompt || action.placeholder };
      return apiFetch<AiOut>(action.path, {
        method: "POST",
        token: getToken(),
        body: JSON.stringify(body),
      });
    },
    onSuccess: (data) => setResult(data),
  });

  return (
    <section className="space-y-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Coach Copilot</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Provider-agnostic AI for workouts, nutrition, summaries, and insights.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {actions.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => {
              setAction(a);
              setResult(null);
            }}
            className={`min-h-10 rounded-xl px-3 text-sm font-semibold ${
              action.id === a.id
                ? "bg-forest text-sand dark:bg-lime dark:text-ink"
                : "bg-white/70 text-slate dark:bg-white/5 dark:text-sand/70"
            }`}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div>
        <Label htmlFor="prompt">Prompt</Label>
        <Input
          id="prompt"
          value={prompt}
          placeholder={action.placeholder}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </div>
      <Button disabled={run.isPending} onClick={() => run.mutate()}>
        {run.isPending ? "Generating…" : "Generate"}
      </Button>

      {result && (
        <div className="space-y-2 rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate dark:text-sand/60">
            {result.feature} · {result.provider}
            {result.model ? ` · ${result.model}` : ""}
          </p>
          <pre className="overflow-x-auto whitespace-pre-wrap text-sm text-ink dark:text-sand">
            {JSON.stringify(result.result, null, 2)}
          </pre>
        </div>
      )}
    </section>
  );
}
