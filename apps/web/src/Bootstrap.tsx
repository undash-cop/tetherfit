import { useEffect } from "react";

import { AppRouter } from "@/App";
import { initKeycloak, keycloak, keycloakConfigured } from "@/lib/auth/keycloak";
import { useAuthStore } from "@/stores/auth";

export function Bootstrap() {
  const setReady = useAuthStore((s) => s.setReady);
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);

  useEffect(() => {
    let cancelled = false;

    async function boot() {
      if (!keycloakConfigured) {
        if (!cancelled) {
          setAuthenticated(false);
          setReady(true);
        }
        return;
      }

      try {
        const authed = await initKeycloak();
        if (!cancelled) {
          setAuthenticated(Boolean(authed && keycloak?.authenticated));
        }
      } catch {
        if (!cancelled) setAuthenticated(false);
      } finally {
        if (!cancelled) setReady(true);
      }
    }

    void boot();
    return () => {
      cancelled = true;
    };
  }, [setAuthenticated, setReady]);

  return <AppRouter />;
}
