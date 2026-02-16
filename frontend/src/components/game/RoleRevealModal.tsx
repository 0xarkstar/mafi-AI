import { motion, AnimatePresence } from 'framer-motion'
import { Sword, Eye, Shield } from 'lucide-react'
import type { Role } from '../../lib/types'

interface RoleRevealModalProps {
  isOpen: boolean
  role: Role | null
  onClose: () => void
}

export function RoleRevealModal({ isOpen, role, onClose }: RoleRevealModalProps) {
  if (!role) return null

  const roleConfig =
    role === 'mafia'
      ? {
          label: 'MAFIA',
          desc: 'Eliminate citizens without being caught. Vote strategically during the day.',
          color: 'text-red-500',
          border: 'border-red-500',
          bg: 'bg-red-500/10',
          glow: 'rgba(239,68,68,0.4)',
          icon: <Sword className="w-16 h-16" />,
        }
      : role === 'detective'
      ? {
          label: 'DETECTIVE',
          desc: 'Investigate one player each night to learn their true identity.',
          color: 'text-blue-400',
          border: 'border-blue-400',
          bg: 'bg-blue-500/10',
          glow: 'rgba(96,165,250,0.4)',
          icon: <Eye className="w-16 h-16" />,
        }
      : {
          label: 'CITIZEN',
          desc: 'Find and vote out the Mafia before they eliminate everyone.',
          color: 'text-green-400',
          border: 'border-green-400',
          bg: 'bg-green-500/10',
          glow: 'rgba(74,222,128,0.4)',
          icon: <Shield className="w-16 h-16" />,
        }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.7, opacity: 0, y: 30 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            className="flex flex-col items-center gap-6 text-center max-w-sm px-6"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.3, type: 'spring', stiffness: 300 }}
              className="text-xs font-bold uppercase tracking-[0.3em] text-white/40"
            >
              Your Role
            </motion.div>

            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.5, type: 'spring', stiffness: 200, damping: 15 }}
              className={`w-28 h-28 rounded-full ${roleConfig.border} border-2 ${roleConfig.bg} flex items-center justify-center ${roleConfig.color}`}
              style={{ boxShadow: `0 0 60px ${roleConfig.glow}` }}
            >
              {roleConfig.icon}
            </motion.div>

            <motion.h2
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.8 }}
              className={`text-5xl font-black tracking-[0.2em] ${roleConfig.color}`}
              style={{ textShadow: `0 0 30px ${roleConfig.glow}` }}
            >
              {roleConfig.label}
            </motion.h2>

            <motion.p
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.0 }}
              className="text-white/50 text-sm leading-relaxed max-w-[280px]"
            >
              {roleConfig.desc}
            </motion.p>

            <motion.button
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.3 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className={`mt-4 px-10 py-3 rounded-full ${roleConfig.border} border ${roleConfig.bg} ${roleConfig.color} font-bold text-sm uppercase tracking-widest hover:bg-white/10 transition-colors`}
            >
              Start Game
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
