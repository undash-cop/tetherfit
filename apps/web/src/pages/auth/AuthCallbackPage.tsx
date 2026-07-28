import { useEffect } from "react";
import { useNavigate } from "react-router";

import { keycloak } from "@/lib/auth/keycloak";
import { useAuthStore } from "@/stores/auth";

/**
 * Legacy callback route. Prefer redirectUri=/app after login.
 * Waits for Keycloak bootstrap before deciding where to go (avoids login loops).
 */
export function AuthCallbackPage() {
  const navigate = useNavigate();
  const ready = useAuthStore((s) => s.ready);
  const authenticated = useAuthStore((s) => s.authenticated);
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);

  useEffect(() => {
    if (!ready) return;

    if (authenticated || keycloak?.authenticated) {
      setAuthenticated(true);
      void navigate("/app", { replace: true });
      return;
    }

    // Auth failed or code already consumed — stop the loop; show login once.
    void navigate("/login", { replace: true });
  }, [ready, authenticated, navigate, setAuthenticated]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-fog dark:bg-ink">
      <p className="font-display text-2xl text-forest dark:text-lime">Completing sign-in…</p>
    </div>
  );
}
