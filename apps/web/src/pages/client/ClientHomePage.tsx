import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Home = {
  full_name: string;
  organization_name: string;
  remaining_credits: number;
  upcoming_sessions: number;
  active_workouts: number;
};

export function ClientHomePage() {
  const home = useQuery({
    queryKey: ["portal-home"],
    queryFn: () => apiFetch<Home>("/api/v1/portal/home", { token: getToken() }),
  });

  if (home.isLoading) return <p>Loading…</p>;
  if (!home.data) return <p>Link your client profile to continue.</p>;

  return (
    <section className="space-y-4">
      <div>
        <p className="text-sm text-slate dark:text-sand/60">{home.data.organization_name}</p>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">
          Hi, {home.data.full_name.split(" ")[0]}
        </h1>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Stat label="Credits" value={home.data.remaining_credits} />
        <Stat label="Upcoming" value={home.data.upcoming_sessions} />
        <Stat label="Workouts" value={home.data.active_workouts} />
      </div>
      <div className="grid gap-2">
        <Link to="/client/book">
          <Button className="w-full">Book a session</Button>
        </Link>
        <Link to="/client/progress">
          <Button variant="outline" className="w-full">
            View progress
          </Button>
        </Link>
        <Link to="/client/nutrition">
          <Button variant="ghost" className="w-full">
            Meal plans
          </Button>
        </Link>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-forest/10 bg-white/70 p-3 dark:border-sand/10 dark:bg-white/5">
      <p className="text-[10px] font-semibold uppercase text-slate dark:text-sand/60">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold">{value}</p>
    </div>
  );
}
