import { useState } from 'react'
import { DollarSign } from 'lucide-react'
import { BET_AMOUNTS } from '../../lib/constants'
import { useWallet } from '../../hooks/useWallet'
import { useBetting } from '../../hooks/useBetting'
import { useGameStore } from '../../stores/gameStore'

export function BetSlip() {
  const [selectedAmount, setSelectedAmount] = useState<number>(BET_AMOUNTS[0])
  const { connected, balance } = useWallet()
  const { placeBet, isPlacing } = useBetting()
  const { phase, round } = useGameStore()

  const isGameActive = phase !== 'lobby' && phase !== 'game_over'
  const balanceNum = parseFloat(balance || '0')
  const hasSufficientBalance = balanceNum >= selectedAmount

  const handleBet = async (target: 'mafia' | 'citizens') => {
    if (!connected || !hasSufficientBalance || !isGameActive || isPlacing) return
    await placeBet('side_win', target, selectedAmount, round)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center text-xs text-white/60 uppercase tracking-wide">
        <span>Bet Amount (USDC)</span>
        <span className="text-white/80">
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
            className={`
              px-3 py-2 rounded-lg font-semibold text-sm transition-all
              ${
                selectedAmount === amount
                  ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                  : 'bg-white/10 text-white/80 hover:bg-white/20'
              }
              ${!connected || balanceNum < amount ? 'opacity-40 cursor-not-allowed' : ''}
            `}
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
          className={`
            px-4 py-3 rounded-lg font-bold text-white transition-all
            ${
              !connected || !hasSufficientBalance || !isGameActive || isPlacing
                ? 'bg-red-900/40 cursor-not-allowed opacity-50'
                : 'bg-red-600 hover:bg-red-700 active:scale-95'
            }
          `}
        >
          {isPlacing ? 'Placing...' : 'Bet Mafia'}
        </button>
        <button
          onClick={() => handleBet('citizens')}
          disabled={!connected || !hasSufficientBalance || !isGameActive || isPlacing}
          className={`
            px-4 py-3 rounded-lg font-bold text-white transition-all
            ${
              !connected || !hasSufficientBalance || !isGameActive || isPlacing
                ? 'bg-green-900/40 cursor-not-allowed opacity-50'
                : 'bg-green-600 hover:bg-green-700 active:scale-95'
            }
          `}
        >
          {isPlacing ? 'Placing...' : 'Bet Citizens'}
        </button>
      </div>

      {!connected && (
        <div className="text-center text-amber-400 text-xs mt-2">
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
