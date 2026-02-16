import { useWallet } from '../../hooks/useWallet'
import { OddsBar } from './OddsBar'
import { SuspectList } from './SuspectList'
import { BetSlip } from './BetSlip'
import { BetHistory } from './BetHistory'
import { PayoutCard } from './PayoutCard'
import { Wallet } from 'lucide-react'
import { cn } from '../../lib/utils'

export function BettingPanel() {
  const { connected, connect, isConnecting } = useWallet()

  return (
    <div className="glass-card p-6 space-y-6 backdrop-blur-lg border border-[#D4A853]/20">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-[#D4A853] tracking-wider text-glow">
          BETTING TERMINAL
        </h2>
      </div>

      {!connected ? (
        <div className="text-center py-12 space-y-4">
          <Wallet className="w-12 h-12 text-[#D4A853]/60 mx-auto" />
          <div className="text-white/60">Connect wallet to start betting</div>
          <button
            onClick={connect}
            disabled={isConnecting}
            className={cn(
              'px-6 py-3 font-semibold rounded-lg transition-all',
              'bg-gradient-to-r from-[#9a7a3a] to-[#D4A853]',
              'hover:from-[#D4A853] hover:to-[#f0d78c]',
              'text-white disabled:opacity-50 disabled:cursor-not-allowed',
              'active:scale-95'
            )}
          >
            {isConnecting ? 'Connecting...' : 'Connect Wallet'}
          </button>
        </div>
      ) : (
        <>
          <OddsBar />
          <SuspectList />
          <BetSlip />
          <PayoutCard />
          <BetHistory />
        </>
      )}
    </div>
  )
}
