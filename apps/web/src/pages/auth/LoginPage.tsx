import { useEffect } from "react";
import { useNavigate } from "react-router";

import { login } from "@/lib/auth/keycloak";
import { useAuthStore } from "@/stores/auth";

export function LoginPage() {
  const authenticated = useAuthStore((s) => s.authenticated);
  const navigate = useNavigate();

  useEffect(() => {
    if (authenticated) {
      void navigate("/app", { replace: true });
      return;
    }
    void login().catch(() => {
      // Config missing — stay on page with message
    });
  }, [authenticated, navigate]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-fog px-5 dark:bg-ink">
      <div className="max-w-md text-center">
        <p className="font-display text-3xl font-bold text-forest dark:text-lime">Signing in…</p>
        <p className="mt-3 text-slate dark:text-sand/70">
          Redirecting to Keycloak. Ensure <code>VITE_KEYCLOAK_*</code> is configured.
        </p>
      </div>
    </div>
  );
}
