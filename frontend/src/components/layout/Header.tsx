import { GlassCard } from '../ui/GlassCard'
import { usePhaseTheme } from '../../hooks/usePhaseTheme'
import { useGameStore } from '../../stores/gameStore'
import { useBettingStore } from '../../stores/bettingStore'
import { useWalletStore } from '../../stores/walletStore'
import { AnimatedNumber } from '../ui/AnimatedNumber'
import { ConnectButton } from '../wallet/ConnectButton'

export function Header() {
  const { icon, label } = usePhaseTheme()
  const round = useGameStore((s) => s.round)
  const balance = useBettingStore((s) => s.balance)
  const walletConnected = useWalletStore((s) => s.connected)
  const walletBalance = useWalletStore((s) => s.balance)

  return (
    <header className="sticky top-0 z-40 p-4">
      <GlassCard className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <h1
              className="text-xl font-black tracking-tight text-transparent bg-clip-text text-glow"
              style={{
                backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
              }}
            >
              MAFI-AI
            </h1>
          </div>

          {/* Phase indicator (center on desktop) */}
          <div className="hidden lg:flex items-center gap-2 absolute left-1/2 -translate-x-1/2">
            <span className="text-2xl">{icon}</span>
            <div className="text-center">
              <div className="text-sm font-semibold text-zinc-100">{label}</div>
              {round > 0 && <div className="text-xs text-zinc-400">Round {round}</div>}
            </div>
          </div>

          {/* Phase indicator (mobile - condensed) */}
          <div className="flex lg:hidden items-center gap-2">
            <span className="text-lg">{icon}</span>
            <span className="text-sm font-medium text-zinc-100">{label}</span>
          </div>

          {/* Status indicators */}
          <div className="hidden lg:flex items-center gap-4">
            {/* USDC balance */}
            {walletConnected && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <span className="text-amber-500 font-mono font-semibold">$</span>
                <AnimatedNumber value={parseFloat(walletBalance) || balance} format={(n) => n.toFixed(2)} />
                <span className="text-xs text-amber-400/80">USDC</span>
              </div>
            )}

            {/* Wallet connect */}
            <ConnectButton />
          </div>
        </div>
      </GlassCard>
    </header>
  )
}
