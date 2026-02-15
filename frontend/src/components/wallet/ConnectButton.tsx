import { Wallet, AlertTriangle, Loader2 } from 'lucide-react'
import { useWallet } from '../../hooks/useWallet'
import { MONAD_TESTNET } from '../../lib/blockchain'

interface ConnectButtonProps {
  mode?: 'default' | 'landing'
}

export function ConnectButton({ mode = 'default' }: ConnectButtonProps) {
  const { connected, address, balance, isConnecting, connect, disconnect } = useWallet()
  const isLanding = mode === 'landing'

  const truncateAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  // Check if on wrong network
  const isWrongNetwork = connected && window.ethereum
  const chainId = window.ethereum?.chainId

  if (connected && address) {
    return (
      <div className={`flex ${isLanding ? 'w-full flex-col gap-2' : 'items-center gap-2'}`}>
        {isWrongNetwork && chainId !== MONAD_TESTNET.chainId && (
          <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-600/20 text-amber-300 text-xs border border-amber-400/20">
            <AlertTriangle className="w-3 h-3" />
            Switch to Monad
          </div>
        )}
        <button
          onClick={disconnect}
          className={`btn-wallet btn-wallet-connected ${isLanding ? 'btn-wallet-landing' : ''}`}
        >
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-white font-medium text-sm">
              {truncateAddress(address)}
            </span>
          </div>
          {!isLanding && (
            <div className="text-white/60 text-xs">
              ${parseFloat(balance || '0').toFixed(2)} USDC
            </div>
          )}
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={connect}
      disabled={isConnecting}
      className={`btn-wallet ${isLanding ? 'btn-wallet-landing' : ''} ${isConnecting ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      {isConnecting ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          Connecting...
        </>
      ) : (
        <>
          <Wallet className="w-4 h-4" />
          Connect Wallet
        </>
      )}
    </button>
  )
}
