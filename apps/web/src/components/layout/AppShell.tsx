import { CalendarDays, CreditCard, Home, Plus, UserRound, Users, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router";

import { InstallPrompt, OfflineBanner } from "@/components/offline/OfflineChrome";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";

const tabs = [
  { to: "/app", label: "Home", icon: Home, end: true },
  { to: "/app/calendar", label: "Calendar", icon: CalendarDays },
  { to: "/app/clients", label: "Clients", icon: Users },
  { to: "/app/payments", label: "Payments", icon: CreditCard },
  { to: "/app/profile", label: "Profile", icon: UserRound },
];

export function AppShell() {
  const toggleTheme = useAuthStore((s) => s.toggleTheme);
  const [fabOpen, setFabOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const hideChrome = location.pathname.startsWith("/app/onboarding");

  if (hideChrome) {
    return <Outlet />;
  }

  return (
    <div className="relative mx-auto min-h-dvh max-w-lg bg-fog text-ink dark:bg-ink dark:text-sand md:max-w-3xl">
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-forest/10 bg-fog/90 px-4 py-3 backdrop-blur dark:border-sand/10 dark:bg-ink/90">
        <p className="font-display text-xl font-bold text-forest dark:text-lime">TetherFit</p>
        <button
          type="button"
          onClick={toggleTheme}
          className="min-h-11 rounded-xl px-3 text-sm font-medium text-slate dark:text-sand/80"
        >
          Theme
        </button>
      </header>

      <main className="px-4 pb-28 pt-4">
        <OfflineBanner />
        <InstallPrompt />
        <Outlet />
      </main>

      <button
        type="button"
        aria-label="Quick action"
        onClick={() => setFabOpen(true)}
        className="fixed bottom-24 right-5 z-30 flex h-14 w-14 items-center justify-center rounded-full bg-lime text-ink shadow-lg shadow-forest/20 md:right-[calc(50%-22rem)]"
      >
        <Plus className="h-6 w-6" />
      </button>

      {fabOpen && (
        <div className="fixed inset-0 z-40 bg-ink/40" onClick={() => setFabOpen(false)}>
          <div
            className="absolute inset-x-4 bottom-28 mx-auto max-w-lg space-y-2 rounded-3xl bg-fog p-4 dark:bg-forest md:max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <p className="font-display text-lg font-bold">Quick actions</p>
              <button type="button" onClick={() => setFabOpen(false)} aria-label="Close">
                <X className="h-5 w-5" />
              </button>
            </div>
            <Button
              className="w-full"
              onClick={() => {
                setFabOpen(false);
                void navigate("/app/clients/new");
              }}
            >
              New client
            </Button>
            <Button
              className="w-full"
              variant="secondary"
              onClick={() => {
                setFabOpen(false);
                void navigate("/app/calendar?book=1");
              }}
            >
              Book session
            </Button>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => {
                setFabOpen(false);
                void navigate("/app/ai");
              }}
            >
              Coach Copilot
            </Button>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => {
                setFabOpen(false);
                void navigate("/app/workouts");
              }}
            >
              Workouts
            </Button>
            <Link to="/app/analytics" onClick={() => setFabOpen(false)}>
              <Button className="w-full" variant="ghost">
                Analytics
              </Button>
            </Link>
            <Link to="/app/clients" onClick={() => setFabOpen(false)}>
              <Button className="w-full" variant="outline">
                View clients
              </Button>
            </Link>
          </div>
        </div>
      )}

      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-forest/10 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur dark:border-sand/10 dark:bg-ink/95">
        <ul className="mx-auto flex max-w-lg items-stretch justify-between px-2 py-2 md:max-w-3xl">
          {tabs.map((tab) => (
            <li key={tab.to} className="flex-1">
              <NavLink
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  cn(
                    "flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-[11px] font-medium text-slate dark:text-sand/60",
                    isActive && "bg-sand text-forest dark:bg-white/5 dark:text-lime",
                  )
                }
              >
                <tab.icon className="h-5 w-5" />
                {tab.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
