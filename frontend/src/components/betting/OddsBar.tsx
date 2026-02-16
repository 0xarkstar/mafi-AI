import { motion } from 'framer-motion'
import { useBettingStore } from '../../stores/bettingStore'

export function OddsBar() {
  const odds = useBettingStore((s) => s.odds)

  const mafiaPercent = Math.round(odds.mafiaWinProb * 100)
  const citizenPercent = Math.round(odds.citizenWinProb * 100)

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-[#D4A853] uppercase tracking-wider font-semibold">
        <span>Win Probability</span>
      </div>
      <div className="h-8 flex rounded-xl overflow-hidden bg-black/30 border border-[#D4A853]/30 relative">
        <motion.div
          className="bg-red-600 flex items-center justify-start px-3 text-white font-semibold text-sm"
          initial={{ width: '50%' }}
          animate={{ width: `${mafiaPercent}%` }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        >
          Mafia {mafiaPercent}%
        </motion.div>
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-[#D4A853] shadow-[0_0_8px_rgba(212,168,83,0.5)]" />
        <motion.div
          className="bg-green-600 flex items-center justify-end px-3 text-white font-semibold text-sm"
          initial={{ width: '50%' }}
          animate={{ width: `${citizenPercent}%` }}
          transition={{ duration: 0.5, ease: 'easeInOut' }}
        >
          Citizens {citizenPercent}%
        </motion.div>
      </div>
    </div>
  )
}
