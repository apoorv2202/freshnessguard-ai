import { useId } from 'react'

export function LogoMark({ className = 'h-7 w-7' }: { className?: string }) {
  const id = useId()
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#35E1CC" />
          <stop offset="0.55" stopColor="#A99CF7" />
          <stop offset="1" stopColor="#D78AE8" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill={`url(#${id})`} opacity="0.16" />
      <rect x="0.5" y="0.5" width="31" height="31" rx="8.5" fill="none" stroke={`url(#${id})`} opacity="0.55" />
      <path
        d="M16 6l8 3v6c0 5-3.4 8.4-8 10-4.6-1.6-8-5-8-10V9l8-3z"
        fill="none"
        stroke={`url(#${id})`}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M12.5 15.5l2.5 2.5 4.5-5"
        fill="none"
        stroke={`url(#${id})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Logo() {
  return (
    <span className="group inline-flex items-center gap-2.5">
      <LogoMark className="h-7 w-7 transition-transform duration-500 ease-spring group-hover:rotate-[-8deg] group-hover:scale-110" />
      <span className="text-[15px] font-semibold tracking-tight">
        FreshnessGuard<span className="ml-1 text-aurora">AI</span>
      </span>
    </span>
  )
}
