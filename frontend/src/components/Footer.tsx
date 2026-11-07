import { Link } from 'react-router-dom'
import { Logo } from './Logo'
import { NAV_ITEMS } from './Navbar'

export function Footer() {
  return (
    <footer className="border-t border-fg/10">
      <div className="container-page flex flex-col gap-8 py-12 md:flex-row md:items-start md:justify-between">
        <div className="max-w-xs">
          <Link to="/" aria-label="FreshnessGuard AI home" className="inline-block rounded-full">
            <Logo />
          </Link>
          <p className="mt-4 text-sm leading-relaxed text-muted">
            Keep every answer fresh, verified and trustworthy.
          </p>
        </div>

        <nav aria-label="Footer">
          <ul className="flex flex-wrap gap-x-8 gap-y-3">
            {NAV_ITEMS.map(({ to, label }) => (
              <li key={to}>
                <Link to={to} className="text-sm text-muted transition-colors duration-300 hover:text-fg">
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="container-page pb-8">
        <p className="font-mono text-xs text-muted/70">
          © {new Date().getFullYear()} FreshnessGuard AI
        </p>
      </div>
    </footer>
  )
}
