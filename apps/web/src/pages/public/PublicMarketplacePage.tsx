import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";

import { apiFetch } from "@/lib/api";

type Listing = {
  id: string;
  slug: string;
  title: string;
  headline: string | null;
  city: string | null;
  session_rate_paise: number | null;
  specialties: string[];
};

function money(paise: number | null) {
  if (paise == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

export function PublicMarketplacePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["public-marketplace"],
    queryFn: () => apiFetch<Listing[]>("/api/v1/public/marketplace"),
  });

  return (
    <section className="mx-auto max-w-3xl space-y-6 px-5 py-10">
      <div>
        <p className="font-display text-sm font-bold uppercase tracking-wide text-moss">TetherFit</p>
        <h1 className="mt-2 font-display text-4xl font-bold text-forest dark:text-lime">
          Find a coach
        </h1>
        <p className="mt-2 text-slate dark:text-sand/70">
          Browse published trainers and request a session.
        </p>
      </div>
      {isLoading && <p>Loading…</p>}
      <ul className="space-y-3">
        {(data ?? []).map((l) => (
          <li key={l.id}>
            <Link
              to={`/marketplace/${l.slug}`}
              className="block rounded-2xl border border-forest/10 bg-white/70 px-4 py-4 dark:border-sand/10 dark:bg-white/5"
            >
              <p className="font-display text-xl font-bold text-forest dark:text-lime">{l.title}</p>
              <p className="text-sm text-slate dark:text-sand/70">{l.headline}</p>
              <p className="mt-2 text-sm">
                {l.city || "Remote"} · from {money(l.session_rate_paise)}
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
