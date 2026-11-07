import { useEffect, useRef } from 'react'

export function AuroraBackground() {
  const glow = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const motion = window.matchMedia('(prefers-reduced-motion: reduce), (pointer: coarse)')
    let frame = 0
    function move(event: PointerEvent) {
      if (motion.matches) return
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => {
        glow.current?.style.setProperty('--pointer-x', `${event.clientX}px`)
        glow.current?.style.setProperty('--pointer-y', `${event.clientY}px`)
      })
    }
    window.addEventListener('pointermove', move, { passive: true })
    return () => {
      window.removeEventListener('pointermove', move)
      cancelAnimationFrame(frame)
    }
  }, [])
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div ref={glow} className="absolute inset-0 motion-reduce:hidden"
        style={{ background: 'radial-gradient(460px circle at var(--pointer-x, 48%) var(--pointer-y, 25%), rgb(var(--blue) / .13), transparent 75%)' }} />
      {/* Ambient teal → purple glows */}
      <div
        className="absolute -left-[12%] -top-[22%] h-[620px] w-[620px] animate-drift-a rounded-full blur-[120px]"
        style={{ background: 'rgb(var(--teal))', opacity: 'calc(var(--glow-opacity) * 0.8)' }}
      />
      <div
        className="absolute -right-[10%] -top-[18%] h-[560px] w-[560px] animate-drift-b rounded-full blur-[130px]"
        style={{ background: 'rgb(var(--lavender))', opacity: 'var(--glow-opacity)' }}
      />
      <div
        className="absolute left-[30%] top-[38%] h-[420px] w-[520px] animate-drift-a rounded-full blur-[140px]"
        style={{ background: 'rgb(var(--orchid))', opacity: 'calc(var(--glow-opacity) * 0.35)' }}
      />
      <div
        className="absolute -bottom-[25%] left-[-8%] h-[480px] w-[560px] animate-drift-b rounded-full blur-[140px]"
        style={{ background: 'rgb(var(--blue))', opacity: 'calc(var(--glow-opacity) * 0.4)' }}
      />

      {/* Fine grid, faded toward the edges */}
      <div
        className="absolute inset-0 opacity-[0.5]"
        style={{
          backgroundImage:
            'linear-gradient(rgb(var(--fg) / 0.045) 1px, transparent 1px), linear-gradient(90deg, rgb(var(--fg) / 0.045) 1px, transparent 1px)',
          backgroundSize: '64px 64px',
          maskImage: 'radial-gradient(ellipse 70% 60% at 50% 0%, #000 30%, transparent 75%)',
          WebkitMaskImage: 'radial-gradient(ellipse 70% 60% at 50% 0%, #000 30%, transparent 75%)',
        }}
      />
    </div>
  )
}
