import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useGameStore } from '../../stores/gameStore'
import { useWalletStore } from '../../stores/walletStore'
import { GlassCard } from '../ui/GlassCard'
import { Button } from '../ui/Button'
import { Trophy, Shield, Skull, RotateCcw, Home } from 'lucide-react'

export function GameOverScreen() {
  const winner = useGameStore((s) => s.winner)
  const resetGame = useGameStore((s) => s.resetGame)
  const setScreen = useGameStore((s) => s.setScreen)
  const balance = useWalletStore((s) => s.balance)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const isMafiaWin = winner === 'mafia'

  // Canvas Confetti Effect
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const particles: { x: number; y: number; vx: number; vy: number; color: string; size: number }[] = []
    const colors = isMafiaWin
      ? ['#ef4444', '#b91c1c', '#7f1d1d', '#000000']
      : ['#22c55e', '#15803d', '#d4a853', '#ffffff']

    for (let i = 0; i < 150; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height - canvas.height,
        vx: (Math.random() - 0.5) * 3,
        vy: Math.random() * 3 + 2,
        color: colors[Math.floor(Math.random() * colors.length)]!,
        size: Math.random() * 6 + 2,
      })
    }

    let animationId: number
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        p.vy += 0.02 // gravity

        if (p.y > canvas.height) {
          p.y = -20
          p.vx = (Math.random() - 0.5) * 3
        }

        ctx.fillStyle = p.color
        ctx.fillRect(p.x, p.y, p.size, p.size)
      })

      animationId = requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animationId)
      window.removeEventListener('resize', handleResize)
    }
  }, [isMafiaWin])

  const handlePlayAgain = () => {
    resetGame()
    setScreen('landing')
  }

  const handleBackToLobby = () => {
    resetGame()
    setScreen('landing')
  }

  return (
    <div className="h-screen w-full flex items-center justify-center relative overflow-hidden">
      <canvas ref={canvasRef} className="absolute inset-0 z-0 pointer-events-none" />

      {/* Dynamic Background Gradient */}
      <div
        className={`absolute inset-0 opacity-40 bg-gradient-to-b ${
          isMafiaWin ? 'from-red-900/50 to-black' : 'from-green-900/50 to-black'
        } z-0`}
      />

      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', damping: 15 }}
        className="relative z-10 max-w-lg w-full p-6"
      >
        <GlassCard
          className={`p-10 text-center border-t-4 ${
            isMafiaWin
              ? 'border-t-red-500 shadow-[0_0_50px_rgba(239,68,68,0.2)]'
              : 'border-t-green-500 shadow-[0_0_50px_rgba(34,197,94,0.2)]'
          }`}
        >
          <motion.div
            initial={{ y: -20 }}
            animate={{ y: 0 }}
            transition={{ delay: 0.2 }}
            className="mb-6 flex justify-center"
          >
            {isMafiaWin ? (
              <div className="w-24 h-24 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/50">
                <Skull className="w-12 h-12 text-red-500" />
              </div>
            ) : (
              <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center border border-green-500/50">
                <Shield className="w-12 h-12 text-green-500" />
              </div>
            )}
          </motion.div>

          <h1
            className={`text-5xl font-black uppercase mb-2 ${
              isMafiaWin ? 'text-red-500 text-glow-red' : 'text-green-500 text-glow-green'
            }`}
          >
            {isMafiaWin ? 'Mafia Wins' : 'Citizens Win'}
          </h1>
          <p className="text-white/60 text-sm tracking-widest uppercase mb-8">
            {isMafiaWin ? 'The underworld takes control' : 'Justice has been served'}
          </p>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-white/5 p-4 rounded-xl border border-white/10">
              <div className="text-xs text-white/40 uppercase mb-1">Total Winnings</div>
              <div className="text-2xl font-bold text-gold flex items-center justify-center gap-2">
                <Trophy className="w-5 h-5" /> ${Math.floor(parseFloat(balance) * 1.5)}
              </div>
            </div>
            <div className="bg-white/5 p-4 rounded-xl border border-white/10">
              <div className="text-xs text-white/40 uppercase mb-1">XP Gained</div>
              <div className="text-2xl font-bold text-white">+250 XP</div>
            </div>
          </div>

          <div className="space-y-3">
            <Button
              onClick={handlePlayAgain}
              variant="primary"
              className="w-full"
              icon={<RotateCcw className="w-4 h-4" />}
            >
              Play Again
            </Button>
            <Button
              onClick={handleBackToLobby}
              variant="ghost"
              className="w-full"
              icon={<Home className="w-4 h-4" />}
            >
              Back to Lobby
            </Button>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
