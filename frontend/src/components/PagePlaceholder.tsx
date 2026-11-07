// Temporary scaffold — replace with real page content.
export function PagePlaceholder({ title }: { title: string }) {
  return (
    <section className="grid min-h-[50vh] animate-fade-up place-items-center text-center">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted">FreshnessGuard AI</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
          <span className="text-aurora">{title}</span>
        </h1>
      </div>
    </section>
  )
}
