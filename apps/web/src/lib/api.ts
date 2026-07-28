import { ensureFreshToken, keycloak } from "@/lib/auth/keycloak";
import { cacheJson, enqueueMutation, readCachedJson } from "@/lib/offline";

const API_URL = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const method = (rest.method || "GET").toUpperCase();
  const cacheKey = `api:${method}:${path}`;

  // Refresh before every authenticated call so idle tabs don't hit the API with an expired JWT.
  let bearer = token;
  if (token !== null && keycloak?.authenticated) {
    bearer = (await ensureFreshToken(60)) ?? token;
  }

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...headers,
      },
    });

    if (!response.ok) {
      // One retry after forced refresh — covers race where token expired mid-flight.
      if (response.status === 401 && keycloak?.authenticated) {
        const refreshed = await ensureFreshToken(-1);
        if (refreshed && refreshed !== bearer) {
          const retry = await fetch(`${API_URL}${path}`, {
            ...rest,
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${refreshed}`,
              ...headers,
            },
          });
          if (retry.ok) {
            if (retry.status === 204) return undefined as T;
            const data = (await retry.json()) as T;
            if (method === "GET") cacheJson(cacheKey, data);
            return data;
          }
        }
      }
      let body: unknown = null;
      try {
        body = await response.json();
      } catch {
        body = await response.text();
      }
      throw new ApiError(response.status, `Request failed: ${response.status}`, body);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const data = (await response.json()) as T;
    if (method === "GET") {
      cacheJson(cacheKey, data);
    }
    return data;
  } catch (err) {
    if (method === "GET" && typeof navigator !== "undefined" && !navigator.onLine) {
      const cached = readCachedJson<T>(cacheKey);
      if (cached != null) return cached;
    }
    if (
      method !== "GET" &&
      typeof navigator !== "undefined" &&
      !navigator.onLine &&
      rest.body &&
      typeof rest.body === "string"
    ) {
      enqueueMutation({ url: `${API_URL}${path}`, method, body: rest.body });
      return undefined as T;
    }
    throw err;
  }
}

export type UserMe = {
  id: string;
  keycloak_user_id: string;
  email: string | null;
  full_name: string;
  avatar: string | null;
  timezone: string;
  onboarding_completed: boolean;
  org_role: string;
  roles: string[];
  organization_id: string | null;
  organization: {
    id: string;
    name: string;
    slug: string;
    timezone: string;
    gstin?: string | null;
    business_address?: string | null;
    business_phone?: string | null;
    upi_vpa?: string | null;
    default_gst_pct?: number;
  } | null;
};

export type Client = {
  id: string;
  organization_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  status: string;
  goals: string | null;
  health_history: string | null;
  medical_notes: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  tags: string[];
  avatar: string | null;
  notes: string | null;
  pt_start_at?: string | null;
  pt_end_at?: string | null;
  created_at: string;
  updated_at: string;
  joined_on?: string | null;
  pt_validity?: string;
  sessions_completed?: number;
  amount_paid_paise?: number;
};

export type Page<T> = {
  items: T[];
  meta: { total: number; limit: number; offset: number };
};

export type SessionPackage = {
  id: string;
  organization_id: string;
  client_id: string;
  total_sessions: number;
  remaining_sessions: number;
  notes: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PtSession = {
  id: string;
  organization_id: string;
  client_id: string;
  trainer_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  location: string | null;
  notes: string | null;
  check_in_at: string | null;
  started_at: string | null;
  paused_at?: string | null;
  finished_at: string | null;
  start_latitude?: number | null;
  start_longitude?: number | null;
  start_accuracy_m?: number | null;
  rating: number | null;
  package_id: string | null;
  credit_deducted: boolean;
  client_name: string | null;
};

export type Dashboard = {
  today_sessions: PtSession[];
  upcoming_sessions: PtSession[];
  recent_clients: Client[];
  generated_at: string;
};
