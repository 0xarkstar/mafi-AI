import { cn } from '../../lib/utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
  variant?: 'default' | 'heavy' | 'subtle'
}

export function GlassCard({ children, className, hover, variant = 'default' }: GlassCardProps) {
  const variantStyles = {
    default: 'backdrop-blur-md bg-white/[0.05]',
    heavy: 'backdrop-blur-xl bg-white/[0.08]',
    subtle: 'backdrop-blur-sm bg-white/[0.02]',
  }

  return (
    <div
      className={cn(
        'glass-card relative overflow-hidden',
        variantStyles[variant],
        hover && 'transition-colors duration-200 hover:bg-white/[0.08]',
        className
      )}
    >
      {/* Subtle inner highlight */}
      <div className="absolute inset-0 rounded-xl border border-white/5 pointer-events-none" />
      {children}
    </div>
  )
}
