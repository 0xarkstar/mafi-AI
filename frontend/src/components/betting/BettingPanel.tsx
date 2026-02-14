import { useWallet } from '../../hooks/useWallet'
import { OddsBar } from './OddsBar'
import { SuspectList } from './SuspectList'
import { BetSlip } from './BetSlip'
import { BetHistory } from './BetHistory'
import { PayoutCard } from './PayoutCard'
import { Wallet } from 'lucide-react'

export function BettingPanel() {
  const { connected, connect, isConnecting } = useWallet()

  return (
    <div className="glass-card p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Betting</h2>
      </div>

      {!connected ? (
        <div className="text-center py-12 space-y-4">
          <Wallet className="w-12 h-12 text-white/40 mx-auto" />
          <div className="text-white/60">Connect wallet to start betting</div>
          <button
            onClick={connect}
            disabled={isConnecting}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
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
