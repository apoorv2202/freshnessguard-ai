import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { Logo } from './Logo'
import { ThemeToggle } from './ThemeToggle'

export const NAV_ITEMS = [
  { to: '/', label: 'Home', end: true },
  { to: '/verify', label: 'Verify', end: false },
  { to: '/examples', label: 'Examples', end: false },
  { to: '/integrations', label: 'Integrations', end: false },
] as const

export function Navbar() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const header = useRef<HTMLElement>(null)
  const { pathname } = useLocation()

  useEffect(() => setOpen(false), [pathname])

  useEffect(() => {
    const bar = header.current
    const viewport = bar?.parentElement
    if (!bar || !viewport) return
    const onScroll = () => setScrolled(viewport.scrollTop > 8)
    const updateOffset = () => viewport.style.setProperty('--nav-offset', `${bar.offsetHeight + 12}px`)
    const resize = new ResizeObserver(updateOffset)
    onScroll()
    updateOffset()
    resize.observe(bar)
    viewport.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      resize.disconnect()
      viewport.removeEventListener('scroll', onScroll)
    }
  }, [])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header ref={header} className="sticky top-0 z-50 flex shrink-0 justify-center px-3 pb-2 pt-[max(1rem,env(safe-area-inset-top))] sm:px-4">
      <nav
        aria-label="Primary"
        className={`glass flex w-full max-w-3xl flex-wrap items-center justify-between py-2 pl-3 pr-2 transition-shadow duration-500 sm:pl-5 ${open ? 'rounded-3xl md:rounded-full' : 'rounded-full'} ${
          scrolled ? 'shadow-[0_16px_50px_-16px_rgb(0_0_0/0.6)]' : ''
        }`}
      >
        <Link to="/" aria-label="FreshnessGuard AI home" className="rounded-full">
          <Logo />
        </Link>

        {/* Desktop links */}
        <ul className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  `relative block rounded-full px-3.5 py-1.5 text-sm font-medium transition-all duration-300 ease-spring active:scale-95 ${
                    isActive
                      ? 'bg-fg/[0.08] text-fg shadow-[inset_0_0_0_1px_rgb(var(--fg)/0.06)]'
                      : 'text-muted hover:bg-fg/[0.05] hover:text-fg'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {label}
                    <span
                      aria-hidden="true"
                      className={`absolute inset-x-4 -bottom-px h-px bg-gradient-to-r from-transparent via-teal to-transparent transition-opacity duration-300 ${
                        isActive ? 'opacity-100' : 'opacity-0'
                      }`}
                    />
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-1.5">
          <ThemeToggle />
          <button
            type="button"
            className="grid h-9 w-9 place-items-center rounded-full border border-fg/10 bg-fg/[0.04] text-muted transition-all duration-300 ease-spring hover:text-fg active:scale-90 md:hidden"
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            aria-controls="mobile-menu"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-[18px] w-[18px]" /> : <Menu className="h-[18px] w-[18px]" />}
          </button>
        </div>

        {/* Mobile menu */}
        {open && (
          <ul
            id="mobile-menu"
            className="mt-2 flex max-h-[50dvh] basis-full flex-col gap-1 overflow-y-auto border-t border-fg/10 pt-2 md:hidden"
          >
            {NAV_ITEMS.map(({ to, label, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `block rounded-2xl px-4 py-3 text-sm font-medium transition-colors ${
                      isActive ? 'bg-fg/[0.08] text-fg' : 'text-muted hover:bg-fg/[0.05] hover:text-fg'
                    }`
                  }
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </header>
  )
}
