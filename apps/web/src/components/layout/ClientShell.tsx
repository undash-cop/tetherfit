import { CalendarDays, Dumbbell, Home, MessageCircle, UserRound, Wallet } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { OfflineBanner } from "@/components/offline/OfflineChrome";
import { cn } from "@/lib/utils";

const tabs = [
  { to: "/client", label: "Home", icon: Home, end: true },
  { to: "/client/workouts", label: "Workouts", icon: Dumbbell },
  { to: "/client/book", label: "Book", icon: CalendarDays },
  { to: "/client/chat", label: "Chat", icon: MessageCircle },
  { to: "/client/payments", label: "Pay", icon: Wallet },
  { to: "/client/profile", label: "Profile", icon: UserRound },
];

export function ClientShell() {
  return (
    <div className="relative mx-auto min-h-dvh max-w-lg bg-fog text-ink dark:bg-ink dark:text-sand">
      <header className="sticky top-0 z-20 border-b border-forest/10 bg-fog/90 px-4 py-3 backdrop-blur dark:border-sand/10 dark:bg-ink/90">
        <p className="font-display text-xl font-bold text-forest dark:text-lime">TetherFit Client</p>
      </header>
      <main className="px-4 pb-28 pt-4">
        <OfflineBanner />
        <Outlet />
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-forest/10 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur dark:border-sand/10 dark:bg-ink/95">
        <ul className="mx-auto flex max-w-lg items-stretch justify-between px-1 py-2">
          {tabs.map((tab) => (
            <li key={tab.to} className="flex-1">
              <NavLink
                to={tab.to}
                end={tab.end}
                className={({ isActive }) =>
                  cn(
                    "flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-[10px] font-medium text-slate dark:text-sand/60",
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
