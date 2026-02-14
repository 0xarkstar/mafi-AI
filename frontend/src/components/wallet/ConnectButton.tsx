import { Wallet, AlertTriangle, Loader2 } from 'lucide-react'
import { useWallet } from '../../hooks/useWallet'
import { MONAD_TESTNET } from '../../lib/blockchain'

export function ConnectButton() {
  const { connected, address, balance, isConnecting, connect, disconnect } = useWallet()

  const truncateAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  // Check if on wrong network
  const isWrongNetwork = connected && window.ethereum
  const chainId = window.ethereum?.chainId

  if (connected && address) {
    return (
      <div className="flex items-center gap-2">
        {isWrongNetwork && chainId !== MONAD_TESTNET.chainId && (
          <div className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-600/20 text-amber-400 text-xs">
            <AlertTriangle className="w-3 h-3" />
            Switch to Monad
          </div>
        )}
        <button
          onClick={disconnect}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-white font-medium text-sm">
              {truncateAddress(address)}
            </span>
          </div>
          <div className="text-white/60 text-xs">
            ${parseFloat(balance || '0').toFixed(2)} USDC
          </div>
        </button>
      </div>
    )
  }

  return (
    <button
      onClick={connect}
      disabled={isConnecting}
      className={`
        flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-white transition-all
        ${
          isConnecting
            ? 'bg-blue-600/50 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
        }
      `}
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
