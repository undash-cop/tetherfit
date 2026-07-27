import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/field";
import { apiFetch } from "@/lib/api";

type Listing = {
  slug: string;
  title: string;
  headline: string | null;
  bio: string | null;
  city: string | null;
  session_rate_paise: number | null;
  specialties: string[];
};

export function PublicMarketplaceDetailPage() {
  const { slug } = useParams();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);

  const listing = useQuery({
    queryKey: ["public-listing", slug],
    queryFn: () => apiFetch<Listing>(`/api/v1/public/marketplace/${slug}`),
    enabled: Boolean(slug),
  });

  const inquire = useMutation({
    mutationFn: () =>
      apiFetch(`/api/v1/public/marketplace/${slug}/inquire`, {
        method: "POST",
        body: JSON.stringify({ name, email, message }),
      }),
    onSuccess: () => setSent(true),
  });

  if (listing.isLoading) return <p className="p-6">Loading…</p>;
  if (!listing.data) return <p className="p-6">Listing not found.</p>;

  const l = listing.data;

  return (
    <section className="mx-auto max-w-xl space-y-6 px-5 py-10">
      <Link to="/marketplace" className="text-sm font-semibold text-moss dark:text-lime">
        ← Marketplace
      </Link>
      <div>
        <h1 className="font-display text-4xl font-bold text-forest dark:text-lime">{l.title}</h1>
        <p className="mt-2 text-slate dark:text-sand/70">{l.headline}</p>
        <p className="mt-2 text-sm">{l.city || "Remote"}</p>
        <p className="mt-4 text-base">{l.bio || "Ready to train with you."}</p>
      </div>

      {sent ? (
        <p className="rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
          Inquiry sent. The coach will follow up soon.
        </p>
      ) : (
        <div className="space-y-3 rounded-2xl border border-forest/10 p-4 dark:border-sand/10">
          <h2 className="font-display text-xl font-bold">Request a session</h2>
          <Label>Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
          <Label>Email</Label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Label>Message</Label>
          <Input value={message} onChange={(e) => setMessage(e.target.value)} />
          <Button
            disabled={!name || !email || !message || inquire.isPending}
            onClick={() => inquire.mutate()}
          >
            Send inquiry
          </Button>
        </div>
      )}
    </section>
  );
}
