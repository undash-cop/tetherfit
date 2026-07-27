import { create } from "zustand";

type Theme = "light" | "dark";

type AuthState = {
  ready: boolean;
  authenticated: boolean;
  theme: Theme;
  setReady: (ready: boolean) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

const stored =
  (typeof localStorage !== "undefined" && (localStorage.getItem("tetherfit-theme") as Theme)) ||
  "light";

if (typeof document !== "undefined") {
  applyTheme(stored);
}

export const useAuthStore = create<AuthState>((set, get) => ({
  ready: false,
  authenticated: false,
  theme: stored,
  setReady: (ready) => set({ ready }),
  setAuthenticated: (authenticated) => set({ authenticated }),
  setTheme: (theme) => {
    localStorage.setItem("tetherfit-theme", theme);
    applyTheme(theme);
    set({ theme });
  },
  toggleTheme: () => {
    const next = get().theme === "light" ? "dark" : "light";
    get().setTheme(next);
  },
}));
