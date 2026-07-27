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

export async function initKeycloak(): Promise<boolean> {
  if (!keycloak) {
    return false;
  }
  if (!initPromise) {
    initPromise = keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: false,
      silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
    });
  }
  return initPromise;
}

export async function login() {
  if (!keycloak) {
    throw new Error("Keycloak is not configured. Set VITE_KEYCLOAK_* env vars.");
  }
  await keycloak.login({
    redirectUri: `${window.location.origin}/auth/callback`,
  });
}

export async function logout() {
  if (!keycloak) return;
  await keycloak.logout({ redirectUri: `${window.location.origin}/` });
}

export function getToken(): string | undefined {
  return keycloak?.token;
}
