import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  children: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-gradient-to-r from-emerald-600 to-emerald-500 text-white hover:from-emerald-500 hover:to-emerald-400',
  secondary: 'bg-zinc-700 text-zinc-100 hover:bg-zinc-600',
  danger: 'bg-red-600 text-white hover:bg-red-500',
  ghost: 'bg-transparent text-zinc-300 hover:bg-white/10',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className,
  disabled,
  type,
  onClick,
}: ButtonProps) {
  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      className={cn(
        'rounded-lg font-semibold transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={disabled}
      type={type}
      onClick={onClick}
    >
      {children}
    </motion.button>
  )
}
