import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'gold'
type ButtonSize = 'sm' | 'md' | 'lg' | 'xl'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: React.ReactNode
  icon?: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-[#0f172a]/80 border border-white/10 text-white hover:bg-[#1e293b] hover:border-gold/60 hover:text-gold hover:shadow-[0_0_20px_rgba(212,168,83,0.15)] active:scale-[0.98]',
  secondary: 'bg-white/5 border border-white/5 text-white/60 hover:text-white hover:bg-white/10 hover:border-white/20',
  danger: 'bg-red-900/20 border border-red-500/20 text-red-400 hover:bg-red-900/40 hover:border-red-500/50',
  ghost: 'bg-transparent border border-transparent text-white/40 hover:text-white/80',
  gold: 'bg-gradient-to-r from-gold-dark to-gold text-white hover:from-gold hover:to-gold-light border border-gold/30',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-4 py-2 text-[10px]',
  md: 'px-6 py-3 text-xs',
  lg: 'px-8 py-4 text-sm',
  xl: 'px-8 py-5 text-sm md:text-base',
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className,
  disabled,
  type,
  onClick,
  icon,
}: ButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.01 }}
      whileTap={disabled ? {} : { scale: 0.99 }}
      className={cn(
        'relative font-bold uppercase tracking-[0.15em] transition-all duration-300',
        'flex items-center justify-center gap-3 rounded-md',
        'disabled:opacity-50 disabled:cursor-not-allowed group overflow-hidden',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {/* Hover shine effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out pointer-events-none" />

      {icon && <span className="w-5 h-5 opacity-70 group-hover:opacity-100 transition-opacity">{icon}</span>}
      {children}
    </motion.button>
  )
}
