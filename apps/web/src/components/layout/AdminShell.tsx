import { NavLink, Outlet } from "react-router";

import { cn } from "@/lib/utils";

const links = [
  { to: "/admin", label: "Usage", end: true },
  { to: "/admin/organizations", label: "Orgs" },
  { to: "/admin/flags", label: "Flags" },
  { to: "/admin/tickets", label: "Support" },
];

export function AdminShell() {
  return (
    <div className="mx-auto min-h-dvh max-w-4xl bg-fog px-4 text-ink dark:bg-ink dark:text-sand">
      <header className="flex items-center justify-between border-b border-forest/10 py-4 dark:border-sand/10">
        <p className="font-display text-2xl font-bold text-forest dark:text-lime">Platform Admin</p>
        <nav className="flex gap-2">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                cn(
                  "rounded-xl px-3 py-2 text-sm font-semibold text-slate dark:text-sand/70",
                  isActive && "bg-forest text-sand dark:bg-lime dark:text-ink",
                )
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="py-6">
        <Outlet />
      </main>
    </div>
  );
}
