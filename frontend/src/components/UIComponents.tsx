import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { motion, HTMLMotionProps } from 'framer-motion';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Glass Card ---
export const GlassCard = ({ children, className, blur = 'md' }: { children: React.ReactNode; className?: string; blur?: 'sm' | 'md' | 'xl' }) => {
  const blurClass = blur === 'xl' ? 'backdrop-blur-xl' : blur === 'md' ? 'backdrop-blur-md' : 'backdrop-blur-sm';
  return (
    <div className={cn(
      `bg-glass-surface ${blurClass} border border-glass-border rounded-xl shadow-2xl relative overflow-hidden`,
      className
    )}>
      {/* Subtle inner highlight */}
      <div className="absolute inset-0 rounded-xl border border-white/5 pointer-events-none" />
      {children}
    </div>
  );
};

// --- Buttons ---
interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button = ({ children, className, variant = 'primary', size = 'md', icon, ...props }: ButtonProps) => {
  const baseStyles = "relative font-bold uppercase tracking-[0.15em] transition-all duration-300 flex items-center justify-center gap-3 rounded-md disabled:opacity-50 disabled:cursor-not-allowed group overflow-hidden border";

  const variants = {
    primary: "bg-[#0f172a]/80 border-white/10 text-white hover:bg-[#1e293b] hover:border-gold/60 hover:text-gold hover:shadow-[0_0_20px_rgba(212,168,83,0.15)] active:scale-[0.98]",
    secondary: "bg-white/5 border-white/5 text-white/60 hover:text-white hover:bg-white/10 hover:border-white/20",
    ghost: "bg-transparent border-transparent text-white/40 hover:text-white/80",
    danger: "bg-red-900/20 border-red-500/20 text-red-400 hover:bg-red-900/40 hover:border-red-500/50"
  };

  const sizes = {
    sm: "px-4 py-2 text-[10px]",
    md: "px-6 py-3 text-xs",
    lg: "px-8 py-4 text-sm",
    xl: "px-8 py-5 text-sm md:text-base",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    >
      {/* Hover Shine Effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out pointer-events-none" />

      {icon && <span className="w-5 h-5 opacity-70 group-hover:opacity-100 transition-opacity">{icon}</span>}
      {children}
    </motion.button>
  );
};

// --- Input ---
export const Input = ({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) => {
  return (
    <div className="relative group w-full">
        <input
        className={cn(
            "w-full bg-black/40 border border-white/10 rounded-md px-4 py-4 text-lg text-white font-bold tracking-wider placeholder:text-white/10 placeholder:font-medium focus:outline-none focus:border-gold/40 focus:bg-black/60 transition-all uppercase",
            className
        )}
        {...props}
        />
        {/* Focus Indicator Line */}
        <div className="absolute bottom-0 left-0 h-[2px] w-0 bg-gold/70 transition-all duration-300 group-focus-within:w-full" />
    </div>
  );
};

// --- Badges ---
export const Badge = ({ children, color = 'gray', className }: { children: React.ReactNode; color?: 'gray' | 'red' | 'green' | 'blue' | 'gold'; className?: string }) => {
  const colors = {
    gray: "bg-white/10 text-white/60 border-white/5",
    red: "bg-red-500/20 text-red-200 border-red-500/30",
    green: "bg-green-500/20 text-green-200 border-green-500/30",
    blue: "bg-blue-500/20 text-blue-200 border-blue-500/30",
    gold: "bg-gold/20 text-gold-light border-gold/30",
  };

  return (
    <span className={cn("px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-bold border", colors[color], className)}>
      {children}
    </span>
  );
};
