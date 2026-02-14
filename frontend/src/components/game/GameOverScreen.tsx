import { motion } from 'framer-motion'
import { Trophy, Skull, Shield } from 'lucide-react'
import { Confetti } from '../ui/Confetti'
import { GlassCard } from '../ui/GlassCard'

interface GameOverScreenProps {
  winner: string
}

export function GameOverScreen({ winner }: GameOverScreenProps) {
  const isMafiaWin = winner === 'mafia'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-md"
    >
      <Confetti active={true} />

      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 150, damping: 20, delay: 0.5 }}
        className="text-center px-4"
      >
        <GlassCard className="p-12 max-w-2xl">
          {/* Icon */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: 'spring', stiffness: 150, damping: 15, delay: 0.7 }}
            className="mb-8"
          >
            {isMafiaWin ? (
              <Skull className="w-32 h-32 mx-auto text-red-500" strokeWidth={1.5} />
            ) : (
              <Shield className="w-32 h-32 mx-auto text-emerald-500" strokeWidth={1.5} />
            )}
          </motion.div>

          {/* Winner text */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.9 }}
          >
            <h1
              className={`text-6xl font-bold mb-4 ${
                isMafiaWin ? 'text-red-500' : 'text-emerald-500'
              }`}
            >
              {isMafiaWin ? 'MAFIA WINS' : 'CITIZENS WIN'}
            </h1>

            <p className="text-xl text-zinc-300 mb-8">
              {isMafiaWin
                ? 'The mafia has taken control of the city'
                : 'The citizens have eliminated all mafia members'}
            </p>
          </motion.div>

          {/* Trophy */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 1.1 }}
          >
            <Trophy className="w-16 h-16 mx-auto text-amber-500" />
          </motion.div>
        </GlassCard>
      </motion.div>
    </motion.div>
  )
}
