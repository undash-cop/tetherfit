import Keycloak from "keycloak-js";

const url = import.meta.env.VITE_KEYCLOAK_URL as string | undefined;
const realm = import.meta.env.VITE_KEYCLOAK_REALM as string | undefined;
const clientId = import.meta.env.VITE_KEYCLOAK_CLIENT_ID as string | undefined;

export const keycloakConfigured = Boolean(url && realm && clientId);

export const keycloak =
  url && realm && clientId
    ? new Keycloak({
        url,
        realm,
        clientId,
      })
    : null;

let initPromise: Promise<boolean> | null = null;
let refreshInFlight: Promise<string | undefined> | null = null;

export async function initKeycloak(): Promise<boolean> {
  if (!keycloak) {
    return false;
  }
  if (!initPromise) {
    // Do not use silentCheckSso / login iframes: Keycloak serves
    // X-Frame-Options: sameorigin, so localhost cannot embed secure.undash-cop.com.
    // Init still completes PKCE code exchange when returning from login redirect.
    initPromise = keycloak
      .init({
        pkceMethod: "S256",
        checkLoginIframe: false,
      })
      .catch((err: unknown) => {
        // Allow a later retry if the first init fails (e.g. network blip).
        initPromise = null;
        throw err;
      });
  }
  return initPromise;
}

/** Refresh the access token if it expires within `minValidity` seconds. */
export async function ensureFreshToken(minValidity = 60): Promise<string | undefined> {
  if (!keycloak?.authenticated) {
    return keycloak?.token;
  }
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    try {
      await keycloak!.updateToken(minValidity);
      return keycloak!.token;
    } catch {
      // Refresh token expired / session gone — leave authenticated flag for callers to handle.
      return keycloak?.token;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

/** Keep tokens alive while the tab is open (covers idle → focus without waiting for an API call). */
export function setupTokenLifecycle(onAuthLost?: () => void) {
  if (!keycloak) return;

  keycloak.onTokenExpired = () => {
    void ensureFreshToken(30).then((token) => {
      if (!token) onAuthLost?.();
    });
  };

  keycloak.onAuthRefreshError = () => {
    onAuthLost?.();
  };

  const onVisible = () => {
    if (document.visibilityState === "visible" && keycloak?.authenticated) {
      void ensureFreshToken(60);
    }
  };
  document.addEventListener("visibilitychange", onVisible);
}

export async function login(redirectPath = "/app") {
  if (!keycloak) {
    throw new Error("Keycloak is not configured. Set VITE_KEYCLOAK_* env vars.");
  }
  // Adapter methods (login/logout) exist only after init completes.
  await initKeycloak();
  const path = redirectPath.startsWith("/") ? redirectPath : `/${redirectPath}`;
  await keycloak.login({
    redirectUri: `${window.location.origin}${path}`,
  });
}

export async function logout() {
  if (!keycloak) return;
  await initKeycloak();
  await keycloak.logout({ redirectUri: `${window.location.origin}/` });
}

export function getToken(): string | undefined {
  return keycloak?.token;
}
