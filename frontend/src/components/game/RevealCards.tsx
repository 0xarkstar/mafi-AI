import { useState } from 'react'
import { motion } from 'framer-motion'
import type { Player } from '../../lib/types'
import { GlassCard } from '../ui/GlassCard'
import { PlayerAvatar } from './PlayerAvatar'

interface RevealCardsProps {
  players: Player[]
}

export function RevealCards({ players }: RevealCardsProps) {
  const [flipped, setFlipped] = useState<Set<string>>(new Set())

  const handleFlip = (name: string) => {
    setFlipped((prev) => new Set(prev).add(name))
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {players.map((player, i) => {
        const isFlipped = flipped.has(player.name)
        const isAI = player.playerType === 'HOUSE_AI' || player.playerType === 'MOLTBOOK_AGENT'

        return (
          <motion.div
            key={player.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="perspective-1000"
            onClick={() => !isFlipped && handleFlip(player.name)}
          >
            <motion.div
              animate={{ rotateY: isFlipped ? 180 : 0 }}
              transition={{ duration: 0.6 }}
              className="relative h-48 cursor-pointer preserve-3d"
            >
              {/* Front - Player Info */}
              <GlassCard className="absolute inset-0 p-4 flex flex-col items-center justify-center backface-hidden">
                <PlayerAvatar
                  name={player.name}
                  color={player.color}
                  isAlive={player.isAlive}
                  size={64}
                />
                <h3 className="mt-3 font-semibold" style={{ color: player.color }}>
                  {player.name}
                </h3>
                {!isFlipped && (
                  <p className="text-xs text-zinc-500 mt-2">Tap to reveal</p>
                )}
              </GlassCard>

              {/* Back - AI or Human */}
              <GlassCard className="absolute inset-0 p-4 flex flex-col items-center justify-center backface-hidden rotate-y-180">
                <div className="text-center">
                  <div className="text-5xl mb-3">{isAI ? '🤖' : '👤'}</div>
                  <div
                    className={`text-2xl font-bold ${
                      isAI ? 'text-purple-400' : 'text-emerald-400'
                    }`}
                  >
                    {isAI ? 'AI' : 'HUMAN'}
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">{player.playerType}</p>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )
      })}
    </div>
  )
}
