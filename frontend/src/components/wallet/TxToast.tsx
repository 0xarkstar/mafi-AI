import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, X, Loader2 } from 'lucide-react'
import { useWalletStore } from '../../stores/walletStore'
import { cn } from '../../lib/utils'

export function TxToast() {
  const txStatus = useWalletStore((s) => s.txStatus)
  const setTxStatus = useWalletStore((s) => s.setTxStatus)

  useEffect(() => {
    if (!txStatus) return

    // Auto-dismiss
    const timeout = txStatus.type === 'success' ? 3000 : txStatus.type === 'error' ? 5000 : 0
    if (timeout > 0) {
      const timer = setTimeout(() => {
        setTxStatus(null)
      }, timeout)
      return () => clearTimeout(timer)
    }
  }, [txStatus, setTxStatus])

  return (
    <AnimatePresence>
      {txStatus && (
        <motion.div
          initial={{ opacity: 0, y: -20, x: '50%' }}
          animate={{ opacity: 1, y: 0, x: '50%' }}
          exit={{ opacity: 0, y: -20, x: '50%' }}
          className="fixed top-4 left-1/2 z-50"
          style={{ translateX: '-50%' }}
        >
          <div
            className={cn(
              'px-4 py-3 rounded-lg shadow-lg backdrop-blur-md flex items-center gap-3 min-w-64 border-2',
              txStatus.type === 'pending' && 'bg-[#D4A853]/90 text-white border-[#f0d78c]',
              txStatus.type === 'success' && 'bg-green-600/90 text-white border-green-400',
              txStatus.type === 'error' && 'bg-red-600/90 text-white border-red-400'
            )}
          >
            {txStatus.type === 'pending' && <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />}
            {txStatus.type === 'success' && <Check className="w-5 h-5 flex-shrink-0" />}
            {txStatus.type === 'error' && <X className="w-5 h-5 flex-shrink-0" />}
            <span className="font-medium text-sm">{txStatus.message}</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
