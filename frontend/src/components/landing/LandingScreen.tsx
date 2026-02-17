import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Gamepad2, Eye, ChevronRight } from 'lucide-react'
import { useWalletStore } from '../../stores/walletStore'
import { useGameStore } from '../../stores/gameStore'
import { ConnectButton } from '../wallet/ConnectButton'
import { useWebSocket } from '../../hooks/useWebSocket'

type Step = 'wallet' | 'nickname' | 'ready'

export function LandingScreen() {
  const [step, setStep] = useState<Step>('wallet')
  const [nickname, setNickname] = useState('')
  const connected = useWalletStore((s) => s.connected)
  const setPhase = useGameStore((s) => s.setPhase)
  const { send } = useWebSocket()

  // Auto-advance to nickname step when wallet connects
  if (connected && step === 'wallet') {
    setStep('nickname')
  }

  const handleConfirmNickname = () => {
    if (!nickname.trim()) return
    setStep('ready')
  }

  const handleJoin = () => {
    send({ type: 'join_lobby', name: nickname.trim() })
    setPhase('lobby', 0)
  }

  const handleSpectate = () => {
    setPhase('lobby', 0)
  }

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#06060c] flex flex-col lg:flex-row">

      {/* ── Left Panel ── */}
      <div className="relative z-10 w-full lg:w-[45%] h-1/2 lg:h-full flex items-center justify-center px-8 lg:px-16">
        <div className="w-full max-w-[420px]">

          {/* Title */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
            className="text-center mb-10"
          >
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-extrabold mb-3 tracking-tight title-glow">
              <span className="bg-gradient-to-b from-[#f0d78c] via-[#d4a853] to-[#9a7a3a] bg-clip-text text-transparent">
                MAFI-AI
              </span>
            </h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 1 }}
              className="text-[#5a5a6e] text-sm tracking-[0.18em] uppercase font-light"
            >
              Can you tell who&apos;s real?
            </motion.p>
          </motion.div>

          {/* Controls Card */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="glass-panel p-8 md:p-10"
          >
            <AnimatePresence mode="wait">

              {/* ── Step 1: Wallet ── */}
              {step === 'wallet' && (
                <motion.div
                  key="wallet"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="w-2 h-2 rounded-full bg-[#6a6a7e]" />
                      <span className="text-[11px] uppercase tracking-[0.15em] text-[#6a6a7e] font-medium">
                        Identity Verification
                      </span>
                    </div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-[#4a4a5e] font-medium">
                      Offline
                    </span>
                  </div>
                  <div className="divider-gold" />
                  <ConnectButton mode="landing" />
                </motion.div>
              )}

              {/* ── Step 2: Nickname ── */}
              {step === 'nickname' && (
                <motion.div
                  key="nickname"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="w-2 h-2 rounded-full bg-[#d4a853] animate-pulse" />
                      <span className="text-[11px] uppercase tracking-[0.15em] text-[#8a8a9e] font-medium">
                        Identity Verified
                      </span>
                    </div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-[#d4a853] font-semibold">
                      Online
                    </span>
                  </div>
                  <div className="divider-gold" />
                  <div className="space-y-3">
                    <label className="text-[11px] uppercase tracking-[0.15em] text-[#6a6a7e] font-semibold">
                      Agent Codename
                    </label>
                    <input
                      type="text"
                      value={nickname}
                      onChange={(e) => setNickname(e.target.value.slice(0, 12))}
                      onKeyDown={(e) => e.key === 'Enter' && handleConfirmNickname()}
                      placeholder="ENTER ALIAS"
                      maxLength={12}
                      autoFocus
                      className="input-premium w-full px-5 py-5 text-lg tracking-widest uppercase placeholder:normal-case placeholder:tracking-widest"
                    />
                  </div>
                  <motion.button
                    whileHover={nickname.trim() ? { scale: 1.02 } : {}}
                    whileTap={nickname.trim() ? { scale: 0.98 } : {}}
                    onClick={handleConfirmNickname}
                    disabled={!nickname.trim()}
                    className="btn-primary w-full py-5 text-sm flex items-center justify-center gap-2.5"
                  >
                    Confirm
                    <ChevronRight className="w-5 h-5" />
                  </motion.button>
                </motion.div>
              )}

              {/* ── Step 3: Ready ── */}
              {step === 'ready' && (
                <motion.div
                  key="ready"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-6"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="w-2 h-2 rounded-full bg-[#d4a853] animate-pulse" />
                      <span className="text-[11px] uppercase tracking-[0.15em] text-[#8a8a9e] font-medium">
                        Agent Ready
                      </span>
                    </div>
                    <span className="text-[11px] uppercase tracking-[0.12em] text-[#d4a853] font-semibold">
                      {nickname.toUpperCase()}
                    </span>
                  </div>
                  <div className="divider-gold" />
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleJoin}
                    className="btn-primary w-full py-5 text-sm flex items-center justify-center gap-2.5"
                  >
                    <Gamepad2 className="w-5 h-5" />
                    Enter Lobby
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleSpectate}
                    className="btn-secondary w-full py-4 text-xs flex items-center justify-center gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    Spectate Match
                  </motion.button>
                </motion.div>
              )}

            </AnimatePresence>
          </motion.div>
        </div>

        {/* Bottom credit */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-6 left-0 right-0 text-center text-[#2a2a3e] text-[10px] tracking-[0.25em] uppercase"
        >
          Powered by AI on Monad
        </motion.p>
      </div>

      {/* ── Right Panel: Image ── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        className="relative w-full lg:w-[55%] h-1/2 lg:h-full"
      >
        <img
          src="/images/landing-bg.png"
          alt=""
          className="absolute inset-0 w-full h-full object-cover object-top pointer-events-none select-none"
        />
        <div className="absolute inset-y-0 left-0 w-2/5 bg-gradient-to-r from-[#06060c] to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-[#06060c] to-transparent" />
        <div className="absolute inset-x-0 top-0 h-1/6 bg-gradient-to-b from-[#06060c]/50 to-transparent" />
        <div className="absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-[#06060c]/30 to-transparent" />
      </motion.div>

      {/* ── Ambient Particles ── */}
      <div className="absolute inset-0 pointer-events-none z-20">
        <div className="smoke-particle smoke-1" />
        <div className="smoke-particle smoke-2" />
        <div className="smoke-particle smoke-3" />
      </div>
    </div>
  )
}
