import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Moon, Sun, Vote, Trophy } from 'lucide-react'
import { useGameStore } from '../../stores/gameStore'
import type { Phase } from '../../lib/types'

const phaseConfig: Record<Phase, { icon: typeof Moon; label: string; gradient: string }> = {
  lobby: { icon: Vote, label: 'Lobby', gradient: 'from-zinc-900 to-zinc-950' },
  night: { icon: Moon, label: 'Night Phase', gradient: 'from-indigo-950 via-slate-950 to-black' },
  day_discussion: { icon: Sun, label: 'Day Discussion', gradient: 'from-amber-900 via-stone-950 to-black' },
  day_vote: { icon: Vote, label: 'Voting Time', gradient: 'from-red-900 via-stone-950 to-black' },
  reveal: { icon: Trophy, label: 'Reveal Phase', gradient: 'from-purple-900 via-slate-950 to-black' },
  game_over: { icon: Trophy, label: 'Game Over', gradient: 'from-emerald-900 via-slate-950 to-black' },
}

export function PhaseOverlay() {
  const phase = useGameStore((s) => s.phase)
  const [showOverlay, setShowOverlay] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<Phase>(phase)

  useEffect(() => {
    if (phase !== 'lobby' && phase !== currentPhase) {
      setCurrentPhase(phase)
      setShowOverlay(true)
      const timer = setTimeout(() => setShowOverlay(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [phase, currentPhase])

  const config = phaseConfig[currentPhase]
  const Icon = config.icon

  return (
    <AnimatePresence>
      {showOverlay && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={`fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br ${config.gradient}`}
        >
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 1.5, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 200, damping: 20 }}
            className="text-center"
          >
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 150, damping: 15, delay: 0.1 }}
            >
              <Icon className="w-24 h-24 mx-auto mb-6 text-white" strokeWidth={1.5} />
            </motion.div>

            <motion.h2
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-5xl font-bold text-white"
            >
              {config.label}
            </motion.h2>

            {/* Animated stars for night phase */}
            {currentPhase === 'night' && (
              <div className="absolute inset-0 overflow-hidden pointer-events-none">
                {Array.from({ length: 20 }).map((_, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: [0, 1, 0], scale: [0, 1, 0] }}
                    transition={{
                      duration: 2,
                      delay: Math.random() * 0.5,
                      repeat: Infinity,
                      repeatDelay: Math.random() * 2,
                    }}
                    className="absolute w-1 h-1 bg-white rounded-full"
                    style={{
                      left: `${Math.random() * 100}%`,
                      top: `${Math.random() * 100}%`,
                    }}
                  />
                ))}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
