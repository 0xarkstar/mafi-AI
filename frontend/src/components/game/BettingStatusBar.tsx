import { motion } from 'framer-motion'
import { TrendingUp } from 'lucide-react'
import { useBettingStore } from '../../stores/bettingStore'

export function BettingStatusBar() {
  const odds = useBettingStore((s) => s.odds)

  // Calculate percentages
  const mafiaPercent = odds.mafiaWinProb * 100

  // Calculate odds multipliers (inverse of probability)
  const mafiaOdds = odds.mafiaWinProb > 0 ? (1 / odds.mafiaWinProb).toFixed(2) : '0.00'
  const citizenOdds = odds.citizenWinProb > 0 ? (1 / odds.citizenWinProb).toFixed(2) : '0.00'

  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex items-center gap-6 bg-[#0f172a]/60 backdrop-blur-md border border-white/10 px-8 py-3 rounded-full shadow-[0_0_30px_rgba(0,0,0,0.3)] hover:bg-[#0f172a]/80 transition-colors duration-300">
      {/* Left Stats: Mafia */}
      <div className="flex flex-col items-end min-w-[80px]">
        <div className="flex items-center gap-1.5 text-red-500">
          <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Mafia</span>
          <TrendingUp className="w-3 h-3" />
        </div>
        <span className="text-xs font-mono font-bold text-white tracking-tight">{mafiaOdds}x</span>
      </div>

      {/* Bar */}
      <div className="h-1.5 w-[300px] bg-black/50 rounded-full overflow-hidden flex relative border border-white/10 shadow-inner">
        <motion.div
          initial={{ width: `${mafiaPercent}%` }}
          animate={{ width: [`${mafiaPercent}%`, `${Math.max(mafiaPercent - 3, 1)}%`, `${Math.min(mafiaPercent + 1, 99)}%`, `${mafiaPercent}%`] }}
          transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          className="h-full bg-gradient-to-r from-red-800 to-red-500 shadow-[0_0_10px_rgba(239,68,68,0.4)]"
        />
        <div className="flex-1 bg-gradient-to-l from-green-800 to-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]" />
        {/* Center tick */}
        <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-white/20 z-10" />
      </div>

      {/* Right Stats: Citizens */}
      <div className="flex flex-col items-start min-w-[80px]">
        <div className="flex items-center gap-1.5 text-green-500">
          <TrendingUp className="w-3 h-3" />
          <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Citizens</span>
        </div>
        <span className="text-xs font-mono font-bold text-white tracking-tight">{citizenOdds}x</span>
      </div>
    </div>
  )
}
