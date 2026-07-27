const tiers = [
  {
    name: "Solo",
    price: "Coming soon",
    detail: "For independent trainers who want a calm daily OS.",
  },
  {
    name: "Studio",
    price: "Coming soon",
    detail: "For 2–10 trainer teams with shared clients and reporting.",
  },
  {
    name: "Enterprise",
    price: "Talk to us",
    detail: "SSO, advanced permissions, and Undash-Cop ecosystem hooks.",
  },
];

export function PricingPage() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-16">
      <h1 className="font-display text-4xl font-bold text-forest dark:text-lime md:text-5xl">
        Simple pricing
      </h1>
      <p className="mt-3 max-w-xl text-slate dark:text-sand/70">
        Billing integration ships in Phase 2. These tiers are placeholders for go-to-market planning.
      </p>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {tiers.map((tier) => (
          <article
            key={tier.name}
            className="rounded-3xl bg-white/70 p-6 shadow-sm shadow-forest/5 dark:bg-white/5"
          >
            <h2 className="font-display text-2xl font-bold">{tier.name}</h2>
            <p className="mt-3 text-3xl font-semibold text-moss dark:text-lime">{tier.price}</p>
            <p className="mt-3 text-sm text-slate dark:text-sand/70">{tier.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
