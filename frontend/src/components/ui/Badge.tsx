import { cn } from '../../lib/utils'

type BadgeVariant = 'alive' | 'dead' | 'mafia' | 'citizen' | 'detective' | 'speaking' | 'human' | 'ai'

interface BadgeProps {
  variant: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
  alive: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  dead: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30',
  mafia: 'bg-red-500/20 text-red-400 border-red-500/30',
  citizen: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  detective: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  speaking: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  human: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  ai: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
}

export function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium',
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  )
}
