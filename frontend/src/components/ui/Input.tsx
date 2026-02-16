import { cn } from '../../lib/utils'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string
}

export function Input({ className, ...props }: InputProps) {
  return (
    <div className="relative group w-full">
      <input
        className={cn(
          'w-full bg-black/40 border border-white/10 rounded-md px-4 py-4',
          'text-lg text-white font-bold tracking-wider',
          'placeholder:text-white/10 placeholder:font-medium',
          'focus:outline-none focus:border-gold/40 focus:bg-black/60',
          'transition-all uppercase',
          className
        )}
        {...props}
      />
      {/* Focus indicator line */}
      <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-gold/70 transition-all duration-300 group-focus-within:w-full" />
    </div>
  )
}
