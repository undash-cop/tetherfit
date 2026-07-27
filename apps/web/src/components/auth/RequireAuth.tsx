import { Navigate, Outlet, useLocation } from "react-router";

import { useMe } from "@/hooks/useMe";
import { useAuthStore } from "@/stores/auth";

export function RequireAuth() {
  const ready = useAuthStore((s) => s.ready);
  const authenticated = useAuthStore((s) => s.authenticated);
  const location = useLocation();
  const me = useMe(ready && authenticated);

  if (!ready) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-fog dark:bg-ink">
        <p className="font-display text-xl text-forest dark:text-lime">Loading…</p>
      </div>
    );
  }

  if (!authenticated) {
    return <Navigate to="/login" replace />;
  }

  if (me.isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-fog dark:bg-ink">
        <p className="font-display text-xl text-forest dark:text-lime">Loading profile…</p>
      </div>
    );
  }

  if (me.isError) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-fog px-5 dark:bg-ink">
        <p className="font-display text-xl text-forest dark:text-lime">Could not reach API</p>
        <p className="text-center text-sm text-slate dark:text-sand/70">
          Check VITE_API_URL and that the API is running with a valid Keycloak token.
        </p>
      </div>
    );
  }

  const roles = new Set(me.data?.roles ?? []);
  const role = me.data?.org_role || "";
  const isClient = role === "client" || (roles.has("client") && !roles.has("business_owner"));
  const isPlatformAdmin = role === "platform_admin" || roles.has("platform_admin");
  const onClient = location.pathname.startsWith("/client");
  const onAdmin = location.pathname.startsWith("/admin");
  const onOnboarding = location.pathname.startsWith("/app/onboarding");

  const needsOnboarding =
    !isClient &&
    !isPlatformAdmin &&
    me.data &&
    (!me.data.onboarding_completed || !me.data.organization_id);

  if (needsOnboarding && !onOnboarding) {
    return <Navigate to="/app/onboarding" replace />;
  }

  if (!needsOnboarding && onOnboarding) {
    return <Navigate to={isClient ? "/client" : "/app"} replace />;
  }

  if (isClient && !onClient && !onOnboarding) {
    return <Navigate to="/client" replace />;
  }

  if (!isClient && onClient) {
    return <Navigate to="/app" replace />;
  }

  if (onAdmin && !isPlatformAdmin) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
