import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { useMe } from "@/hooks/useMe";
import { logout } from "@/lib/auth/keycloak";

const links = [
  ["/app/settings", "Settings"],
  ["/app/scheduling", "Scheduling"],
  ["/app/automations", "Automations"],
  ["/app/chat", "Chat"],
  ["/app/ai", "Coach Copilot"],
  ["/app/analytics", "Analytics"],
  ["/app/integrations", "Integrations"],
  ["/app/marketplace", "Marketplace"],
  ["/app/enterprise", "Enterprise"],
  ["/admin", "Platform Admin"],
  ["/app/workouts", "Workouts"],
  ["/app/nutrition", "Nutrition"],
  ["/app/reports", "Reports"],
] as const;

export function ProfilePage() {
  const me = useMe();

  return (
    <section className="space-y-4">
      <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Profile</h1>
      <div className="rounded-2xl border border-forest/10 bg-white/70 p-4 dark:border-sand/10 dark:bg-white/5">
        <p className="font-semibold text-lg">{me.data?.full_name || "—"}</p>
        <p className="text-sm text-slate dark:text-sand/60">{me.data?.email || "No email"}</p>
        <p className="mt-2 text-sm">Timezone: {me.data?.timezone}</p>
        <p className="text-sm">Org: {me.data?.organization?.name || "—"}</p>
      </div>
      {links.map(([to, label]) => (
        <Link key={to} to={to}>
          <Button variant="outline" className="w-full">
            {label}
          </Button>
        </Link>
      ))}
      <Button variant="secondary" className="w-full" onClick={() => void logout()}>
        Log out
      </Button>
    </section>
  );
}
