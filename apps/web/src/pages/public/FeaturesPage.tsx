const modules = [
  {
    title: "Client CRM",
    body: "Profiles, goals, health history, and progress in one place.",
  },
  {
    title: "Calendar & sessions",
    body: "Book, check in, track workouts, and finish with notes.",
  },
  {
    title: "Workouts & nutrition",
    body: "Plans, templates, and tracking that feel native on mobile.",
  },
  {
    title: "Billing & payments",
    body: "Invoices, packages, and collections without spreadsheet chaos.",
  },
];

export function FeaturesPage() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-16">
      <h1 className="font-display text-4xl font-bold text-forest dark:text-lime md:text-5xl">
        Everything a modern coach needs
      </h1>
      <p className="mt-3 max-w-2xl text-slate dark:text-sand/70">
        One product surface for the work you already do — designed mobile-first, API-first, and ready
        for AI copilots later.
      </p>
      <div className="mt-12 grid gap-8 md:grid-cols-2">
        {modules.map((item) => (
          <article key={item.title} className="border-t border-forest/15 pt-6 dark:border-sand/15">
            <h2 className="font-display text-2xl font-bold text-forest dark:text-sand">
              {item.title}
            </h2>
            <p className="mt-2 text-slate dark:text-sand/70">{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
