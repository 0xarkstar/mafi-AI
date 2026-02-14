import { cn } from '../../lib/utils'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  hover?: boolean
}

export function GlassCard({ children, className, hover }: GlassCardProps) {
  return (
    <div
      className={cn(
        'glass-card',
        hover && 'transition-colors duration-200 hover:bg-white/[0.08]',
        className
      )}
    >
      {children}
    </div>
  )
}
