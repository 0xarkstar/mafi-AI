import { motion } from 'framer-motion'
import { useBettingStore } from '../../stores/bettingStore'
import { useGameStore } from '../../stores/gameStore'

export function SuspectList() {
  const { odds } = useBettingStore()
  const { players } = useGameStore()

  const suspects = Object.entries(odds.mafiaSuspects || {})
    .filter(([name]) => players[name]?.isAlive)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)

  if (suspects.length === 0) {
    return (
      <div className="text-center text-white/40 text-sm py-4">
        No suspicion data yet
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="text-xs text-white/60 uppercase tracking-wide">
        Mafia Suspicion
      </div>
      <div className="space-y-1.5">
        {suspects.map(([name, prob], index) => {
          const player = players[name]
          if (!player) return null

          const percentage = Math.round(prob * 100)

          return (
            <div key={name} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium" style={{ color: player.color }}>
                  #{index + 1} {name}
                </span>
                <span className="text-white/60">{percentage}%</span>
              </div>
              <div className="h-1.5 bg-black/30 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-red-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${percentage}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
