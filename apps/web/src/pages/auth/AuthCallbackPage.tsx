import { useEffect } from "react";
import { useNavigate } from "react-router";

import { keycloak } from "@/lib/auth/keycloak";
import { useAuthStore } from "@/stores/auth";

export function AuthCallbackPage() {
  const navigate = useNavigate();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);

  useEffect(() => {
    if (keycloak?.authenticated) {
      setAuthenticated(true);
      void navigate("/app", { replace: true });
      return;
    }
    void navigate("/login", { replace: true });
  }, [navigate, setAuthenticated]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-fog dark:bg-ink">
      <p className="font-display text-2xl text-forest dark:text-lime">Completing sign-in…</p>
    </div>
  );
}
