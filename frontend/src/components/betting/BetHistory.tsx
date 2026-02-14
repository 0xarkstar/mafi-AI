import { useBettingStore } from '../../stores/bettingStore'
import { Check, X, Loader2 } from 'lucide-react'

export function BetHistory() {
  const bets = useBettingStore((s) => s.bets)

  if (bets.length === 0) {
    return (
      <div className="text-center text-white/40 text-sm py-8">
        No bets placed yet
      </div>
    )
  }

  const recentBets = [...bets].reverse().slice(0, 10)

  return (
    <div className="space-y-2">
      <div className="text-xs text-white/60 uppercase tracking-wide">
        Bet History
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {recentBets.map((bet) => (
          <div
            key={bet.id}
            className="flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
          >
            <div className="flex items-center gap-2 flex-1">
              <div
                className={`
                  px-2 py-0.5 rounded text-xs font-semibold
                  ${bet.target === 'mafia' ? 'bg-red-600/30 text-red-300' : 'bg-green-600/30 text-green-300'}
                `}
              >
                {bet.target}
              </div>
              <span className="text-white font-medium text-sm">
                ${bet.amount}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {bet.status === 'pending' && (
                <div className="flex items-center gap-1 text-amber-400 text-xs">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  <span>Pending</span>
                </div>
              )}
              {bet.status === 'won' && (
                <div className="flex items-center gap-1 text-green-400 text-xs">
                  <Check className="w-3 h-3" />
                  <span>Won</span>
                </div>
              )}
              {bet.status === 'lost' && (
                <div className="flex items-center gap-1 text-red-400 text-xs">
                  <X className="w-3 h-3" />
                  <span>Lost</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
