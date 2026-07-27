import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";
import { getToken } from "@/lib/auth/keycloak";

type Listing = {
  id: string;
  slug: string;
  title: string;
  headline: string | null;
  city: string | null;
  session_rate_paise: number | null;
  is_published: boolean;
};

type Inquiry = {
  id: string;
  name: string;
  email: string;
  message: string;
  status: string;
};

export function MarketplacePage() {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [city, setCity] = useState("");
  const [rate, setRate] = useState(2500);

  const listings = useQuery({
    queryKey: ["marketplace-listings"],
    queryFn: () =>
      apiFetch<Listing[]>("/api/v1/marketplace/listings", { token: getToken() }),
  });
  const inquiries = useQuery({
    queryKey: ["marketplace-inquiries"],
    queryFn: () =>
      apiFetch<Inquiry[]>("/api/v1/marketplace/inquiries", { token: getToken() }),
  });

  const create = useMutation({
    mutationFn: () =>
      apiFetch("/api/v1/marketplace/listings", {
        method: "POST",
        token: getToken(),
        body: JSON.stringify({
          title,
          city,
          session_rate_paise: rate * 100,
          is_published: true,
          specialties: ["personal training"],
          headline: "Book a session on TetherFit",
        }),
      }),
    onSuccess: () => {
      setTitle("");
      void qc.invalidateQueries({ queryKey: ["marketplace-listings"] });
    },
  });

  return (
    <section className="space-y-4">
      <div>
        <h1 className="font-display text-3xl font-bold text-forest dark:text-lime">Marketplace</h1>
        <p className="mt-1 text-sm text-slate dark:text-sand/70">
          Publish your coaching profile and capture inbound inquiries.
        </p>
        <Link to="/marketplace" className="text-sm font-semibold text-moss dark:text-lime">
          View public marketplace →
        </Link>
      </div>

      <div className="space-y-2 rounded-2xl border border-dashed border-forest/20 p-4 dark:border-sand/20">
        <Label>Listing title</Label>
        <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Ada · Strength Coach" />
        <Label>City</Label>
        <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Bengaluru" />
        <Label>Session rate (INR)</Label>
        <Input type="number" value={rate} onChange={(e) => setRate(Number(e.target.value))} />
        <Button disabled={!title || create.isPending} onClick={() => create.mutate()}>
          Publish listing
        </Button>
      </div>

      <ul className="space-y-2">
        {(listings.data ?? []).map((l) => (
          <li key={l.id} className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10">
            <p className="font-semibold">{l.title}</p>
            <p className="text-sm text-slate dark:text-sand/60">
              /marketplace/{l.slug} · {l.city || "—"} ·{" "}
              {l.is_published ? "Published" : "Draft"}
            </p>
          </li>
        ))}
      </ul>

      <h2 className="font-display text-xl font-bold">Inquiries</h2>
      <ul className="space-y-2">
        {(inquiries.data ?? []).map((i) => (
          <li key={i.id} className="rounded-2xl border border-forest/10 px-4 py-3 dark:border-sand/10">
            <p className="font-semibold">
              {i.name} · {i.email}
            </p>
            <p className="text-sm text-slate dark:text-sand/70">{i.message}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
