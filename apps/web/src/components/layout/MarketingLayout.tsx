import { Link, NavLink, Outlet } from "react-router";

import { Button } from "@/components/ui/button";
import { login } from "@/lib/auth/keycloak";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth";

const links = [
  { to: "/features", label: "Features" },
  { to: "/marketplace", label: "Marketplace" },
  { to: "/pricing", label: "Pricing" },
  { to: "/contact", label: "Contact" },
];

export function MarketingLayout() {
  const authenticated = useAuthStore((s) => s.authenticated);

  return (
    <div className="min-h-dvh bg-fog text-ink dark:bg-ink dark:text-sand">
      <header className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Link to="/" className="font-display text-2xl font-extrabold tracking-tight text-forest dark:text-lime">
          TetherFit
        </Link>
        <nav className="hidden items-center gap-6 md:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn(
                  "text-sm font-medium text-slate transition hover:text-forest dark:text-sand/70 dark:hover:text-lime",
                  isActive && "text-forest dark:text-lime",
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          {authenticated ? (
            <Link to="/app">
              <Button variant="secondary">Open app</Button>
            </Link>
          ) : (
            <>
              <Button variant="ghost" onClick={() => void login()}>
                Log in
              </Button>
              <Button onClick={() => void login()}>Start free</Button>
            </>
          )}
        </div>
      </header>
      <Outlet />
      <footer className="mx-auto max-w-6xl px-5 py-12 text-sm text-slate dark:text-sand/60">
        <div className="flex flex-col gap-2 border-t border-forest/10 pt-8 dark:border-sand/10 md:flex-row md:items-center md:justify-between">
          <p className="font-display text-lg text-forest dark:text-lime">TetherFit</p>
          <p>The Operating System for Modern Fitness Professionals</p>
        </div>
      </footer>
    </div>
  );
}
