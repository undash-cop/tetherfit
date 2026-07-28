import { Navigate, Outlet, useLocation } from "react-router";

import { useMe } from "@/hooks/useMe";
import { ApiError } from "@/lib/api";
import { logout } from "@/lib/auth/keycloak";
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
    const err = me.error;
    const status = err instanceof ApiError ? err.status : null;
    const detail =
      err instanceof ApiError && err.body && typeof err.body === "object" && "detail" in err.body
        ? String((err.body as { detail: unknown }).detail)
        : err instanceof Error
          ? err.message
          : "Unknown error";

    const isAuth = status === 401 || status === 403;

    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-fog px-5 dark:bg-ink">
        <p className="font-display text-xl text-forest dark:text-lime">
          {isAuth ? "API rejected your login token" : "Could not reach API"}
        </p>
        <p className="max-w-lg text-center text-sm text-slate dark:text-sand/70">
          {isAuth
            ? "Keycloak realm/issuer on the API must match the SPA. On the VPS set UDC_JWT_ISSUER and KEYCLOAK_REALM to tetherfit, then redeploy."
            : "Check VITE_API_URL, CORS_ORIGINS (include this site), and that the API is up."}
        </p>
        <p className="max-w-lg break-all text-center font-mono text-xs text-slate/80 dark:text-sand/50">
          {status ? `HTTP ${status}: ` : ""}
          {detail}
        </p>
        <button
          type="button"
          className="mt-2 rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-sand dark:bg-lime dark:text-ink"
          onClick={() => void logout()}
        >
          Sign out and try again
        </button>
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
