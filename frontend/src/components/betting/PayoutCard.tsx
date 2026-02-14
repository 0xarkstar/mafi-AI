import { useState } from 'react'
import { DollarSign, Loader2 } from 'lucide-react'
import { useGameStore } from '../../stores/gameStore'
import { useBettingStore } from '../../stores/bettingStore'
import { useWallet } from '../../hooks/useWallet'
import { useWalletStore } from '../../stores/walletStore'
import { createContracts } from '../../lib/blockchain'

export function PayoutCard() {
  const [isClaiming, setIsClaiming] = useState(false)
  const phase = useGameStore((s) => s.phase)
  const bets = useBettingStore((s) => s.bets)
  const { signer, address } = useWallet()
  const setTxStatus = useWalletStore((s) => s.setTxStatus)

  const hasWinningBets = bets.some((bet) => bet.status === 'won')
  const totalWinnings = bets
    .filter((bet) => bet.status === 'won')
    .reduce((sum, bet) => sum + bet.amount * bet.weight, 0)

  if (phase !== 'game_over' || !hasWinningBets) {
    return null
  }

  const handleClaim = async () => {
    if (!signer || !address || isClaiming) return

    setIsClaiming(true)
    setTxStatus({ type: 'pending', message: 'Claiming winnings...' })

    try {
      // Check if blockchain mode is enabled
      const blockchainConfigRes = await fetch('/api/blockchain-config')
      const blockchainConfig = await blockchainConfigRes.json()

      if (blockchainConfig.enabled) {
        const { bettingContract } = createContracts(signer, blockchainConfig.contract_address)

        // Claim on-chain
        const gameId = 1 // TODO: get from game state
        const tx = await bettingContract.claimWinnings!(gameId)
        await tx.wait()

        setTxStatus({ type: 'success', message: 'Winnings claimed successfully!' })
      } else {
        // TODO: Implement X402 claim endpoint
        setTxStatus({ type: 'error', message: 'X402 claim not yet implemented' })
      }

      setTimeout(() => setTxStatus(null), 3000)
    } catch (err: any) {
      console.error('Claim error:', err)
      setTxStatus({ type: 'error', message: err.message || 'Failed to claim winnings' })
      setTimeout(() => setTxStatus(null), 5000)
    } finally {
      setIsClaiming(false)
    }
  }

  return (
    <div className="glass-card p-6 space-y-4 border-2 border-yellow-500/30">
      <div className="text-center">
        <div className="text-xs text-white/60 uppercase tracking-wide mb-2">
          Your Winnings
        </div>
        <div className="text-4xl font-bold text-yellow-400 flex items-center justify-center gap-2">
          <DollarSign className="w-8 h-8" />
          {totalWinnings.toFixed(2)}
        </div>
        <div className="text-xs text-white/40 mt-1">USDC</div>
      </div>

      <button
        onClick={handleClaim}
        disabled={isClaiming || !address}
        className={`
          w-full px-4 py-3 rounded-lg font-bold text-white transition-all
          ${
            isClaiming || !address
              ? 'bg-yellow-900/40 cursor-not-allowed opacity-50'
              : 'bg-yellow-600 hover:bg-yellow-700 active:scale-95'
          }
        `}
      >
        {isClaiming ? (
          <span className="flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Claiming...
          </span>
        ) : (
          'Claim Winnings'
        )}
      </button>
    </div>
  )
}
