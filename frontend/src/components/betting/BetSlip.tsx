import { useState } from 'react'
import { DollarSign } from 'lucide-react'
import { BET_AMOUNTS } from '../../lib/constants'
import { useWallet } from '../../hooks/useWallet'
import { useBetting } from '../../hooks/useBetting'
import { useGameStore } from '../../stores/gameStore'
import { cn } from '../../lib/utils'

export function BetSlip() {
  const [selectedAmount, setSelectedAmount] = useState<number>(BET_AMOUNTS[0])
  const { connected, balance } = useWallet()
  const { placeBet, isPlacing } = useBetting()
  const phase = useGameStore((s) => s.phase)
  const round = useGameStore((s) => s.round)

  const isGameActive = phase !== 'lobby' && phase !== 'game_over'
  const balanceNum = parseFloat(balance || '0')
  const hasSufficientBalance = balanceNum >= selectedAmount

  const handleBet = async (target: 'mafia' | 'citizens') => {
    if (!connected || !hasSufficientBalance || !isGameActive || isPlacing) return
    await placeBet('side_win', target, selectedAmount, round)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center text-xs text-[#D4A853] uppercase tracking-wider">
        <span>Bet Amount (USDC)</span>
        <span className="text-[#f0d78c] font-semibold">
          Balance: ${balance || '0'}
        </span>
      </div>

      {/* Amount selector */}
      <div className="grid grid-cols-3 gap-2">
        {BET_AMOUNTS.map((amount) => (
          <button
            key={amount}
            onClick={() => setSelectedAmount(amount)}
            disabled={!connected || balanceNum < amount}
            className={cn(
              'px-3 py-2 rounded-lg font-semibold text-sm transition-all',
              selectedAmount === amount
                ? 'bg-[#D4A853] text-black ring-2 ring-[#f0d78c]'
                : 'bg-white/5 text-white/80 hover:bg-white/10 border border-white/10',
              (!connected || balanceNum < amount) && 'opacity-40 cursor-not-allowed'
            )}
          >
            <DollarSign className="inline w-3 h-3" />
            {amount}
          </button>
        ))}
      </div>

      {/* Bet buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => handleBet('mafia')}
          disabled={!connected || !hasSufficientBalance || !isGameActive || isPlacing}
          className={cn(
            'px-4 py-3 rounded-lg font-bold text-white transition-all',
            !connected || !hasSufficientBalance || !isGameActive || isPlacing
              ? 'bg-red-900/40 cursor-not-allowed opacity-50'
              : 'bg-red-600 hover:bg-red-700 active:scale-95'
          )}
        >
          {isPlacing ? 'Placing...' : 'Bet Mafia'}
        </button>
        <button
          onClick={() => handleBet('citizens')}
          disabled={!connected || !hasSufficientBalance || !isGameActive || isPlacing}
          className={cn(
            'px-4 py-3 rounded-lg font-bold text-white transition-all',
            !connected || !hasSufficientBalance || !isGameActive || isPlacing
              ? 'bg-green-900/40 cursor-not-allowed opacity-50'
              : 'bg-green-600 hover:bg-green-700 active:scale-95'
          )}
        >
          {isPlacing ? 'Placing...' : 'Bet Citizens'}
        </button>
      </div>

      {!connected && (
        <div className="text-center text-[#D4A853] text-xs mt-2">
          Connect wallet to place bets
        </div>
      )}

      {connected && !hasSufficientBalance && (
        <div className="text-center text-red-400 text-xs mt-2">
          Insufficient USDC balance
        </div>
      )}

      {connected && !isGameActive && (
        <div className="text-center text-white/60 text-xs mt-2">
          Game not active
        </div>
      )}
    </div>
  )
}
