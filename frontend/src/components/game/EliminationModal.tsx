import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import type { Role } from '../../lib/types'
import { GlassCard } from '../ui/GlassCard'
import { Badge } from '../ui/Badge'
import { PlayerAvatar } from './PlayerAvatar'
import { AGENTS } from '../../lib/constants'

interface EliminationModalProps {
  playerName: string
  role: Role
  reason: 'killed_at_night' | 'voted_out'
  onClose: () => void
}

export function EliminationModal({ playerName, role, reason, onClose }: EliminationModalProps) {
  const agentData = AGENTS.find((a) => a.name === playerName)
  const color = agentData?.color || '#71717a'

  useEffect(() => {
    const timer = setTimeout(onClose, 3000)
    return () => clearTimeout(timer)
  }, [onClose])

  const reasonText = reason === 'killed_at_night' ? 'Killed by Mafia' : 'Voted Out'

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, rotateY: 90 }}
          animate={{ scale: 1, opacity: 1, rotateY: 0 }}
          exit={{ scale: 0.9, opacity: 0, rotateY: -90 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-md mx-4"
        >
          <GlassCard className="p-8 relative">
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-zinc-400 hover:text-zinc-200 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center space-y-6">
              {/* Avatar */}
              <div className="flex justify-center">
                <PlayerAvatar name={playerName} color={color} isAlive={false} size={96} />
              </div>

              {/* Name */}
              <div>
                <h2 className="text-2xl font-bold mb-2" style={{ color }}>
                  {playerName}
                </h2>
                <p className="text-zinc-400">{reasonText}</p>
              </div>

              {/* Role reveal */}
              <div className="flex justify-center gap-3">
                <Badge variant={role}>Role: {role.toUpperCase()}</Badge>
              </div>

              {/* Auto-dismiss hint */}
              <p className="text-xs text-zinc-500">Auto-closing in 3s...</p>
            </div>
          </GlassCard>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
