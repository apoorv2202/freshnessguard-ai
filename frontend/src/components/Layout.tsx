import { useLayoutEffect, useRef, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { AuroraBackground } from './AuroraBackground'
import { Footer } from './Footer'
import { Navbar } from './Navbar'
import { Freshie } from './Freshie'
import type { FreshieMood } from './Freshie'

export interface LayoutContext {
  setFreshieMood: (mood: FreshieMood) => void
}

export function Layout() {
  const { pathname } = useLocation()
  const viewport = useRef<HTMLDivElement>(null)
  const [mood, setFreshieMood] = useState<FreshieMood>('idle')
  useLayoutEffect(() => {
    viewport.current?.scrollTo({ top: 0, behavior: 'instant' })
  }, [pathname])

  return (
    <div className="app-shell isolate flex flex-col">
      <AuroraBackground />
      <div ref={viewport} tabIndex={0} role="region" aria-label="Page content"
        className="app-scroll flex min-h-0 flex-1 flex-col overflow-y-auto focus-visible:-outline-offset-2">
        <Navbar />
        <main className="container-page flex-1 pb-16 pt-8 sm:pt-12">
          <Outlet context={{ setFreshieMood } satisfies LayoutContext} />
        </main>
        <Footer />
      </div>
      <Freshie mood={mood} />
    </div>
  )
}
