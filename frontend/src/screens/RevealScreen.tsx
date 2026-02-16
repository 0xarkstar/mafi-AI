import { useState } from 'react'
import { motion } from 'framer-motion'
import { useGameStore } from '../stores/gameStore'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { Bot, User, ArrowRight, Sparkles } from 'lucide-react'
import { AVATAR_IMAGES } from '../lib/constants'
import type { Player } from '../lib/types'

// Card Component with 3D Flip
const RevealCard = ({ player, index }: { player: Player; index: number }) => {
  const [isFlipped, setIsFlipped] = useState(false)

  const isAI = player.playerType === 'house_ai' || player.playerType === 'moltbook_agent'

  return (
    <div
      className="relative w-full aspect-[3/4] cursor-pointer group"
      style={{ perspective: '1000px' }}
      onClick={() => setIsFlipped(!isFlipped)}
    >
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1, duration: 0.5 }}
        className="w-full h-full relative transition-all duration-700"
        style={{
          transformStyle: 'preserve-3d',
          transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
        }}
      >
        {/* Front of Card */}
        <div
          className="absolute inset-0"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <GlassCard className="w-full h-full flex flex-col items-center justify-center gap-4 border-white/10 group-hover:border-gold/30 transition-colors bg-[#0f172a]/80">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-white/10 to-transparent border border-white/10 flex items-center justify-center relative overflow-hidden">
              {/* Animated background glow */}
              <div className="absolute inset-0 bg-gold/10 blur-xl animate-pulse" />
              {player.avatarIndex != null ? (
                <img src={AVATAR_IMAGES[player.avatarIndex]} alt={player.name} className="w-full h-full object-cover relative z-10 rounded-full" />
              ) : (
                <span className="text-3xl font-bold text-white/80 relative z-10">{player.name.charAt(0)}</span>
              )}
            </div>
            <div className="text-center">
              <h3 className="text-xl font-bold text-white mb-1">{player.name}</h3>
              <p className="text-xs text-white/40 uppercase tracking-widest">Tap to reveal</p>
            </div>
            <div className="absolute bottom-4 left-0 right-0 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <Sparkles className="w-4 h-4 text-gold/50" />
            </div>
          </GlassCard>
        </div>

        {/* Back of Card */}
        <div
          className="absolute inset-0"
          style={{
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          <GlassCard className={`w-full h-full flex flex-col items-center justify-center gap-4 border-2 ${isAI ? 'border-purple-500/50 bg-purple-900/20' : 'border-green-500/50 bg-green-900/20'}`}>
            <div className={`w-24 h-24 rounded-full flex items-center justify-center mb-2 ${isAI ? 'bg-purple-500/20' : 'bg-green-500/20'}`}>
              {isAI ? (
                <Bot className="w-12 h-12 text-purple-400" />
              ) : (
                <User className="w-12 h-12 text-green-400" />
              )}
            </div>
            <div className="text-center">
              <h3 className={`text-2xl font-black uppercase tracking-wider mb-2 ${isAI ? 'text-purple-400 text-glow' : 'text-green-400 text-glow-green'}`}>
                {isAI ? 'AI AGENT' : 'HUMAN'}
              </h3>
              <p className="text-xs text-white/60 max-w-[80%] mx-auto leading-relaxed">
                {isAI ? `${player.trait || 'AI'} Model v2.4` : `Verified Player`}
              </p>
              {player.role && (
                <div className={`mt-4 px-3 py-1 rounded-full text-[10px] font-bold uppercase border ${
                  player.role === 'mafia' ? 'border-red-500/50 text-red-400 bg-red-900/20' : 'border-blue-500/50 text-blue-400 bg-blue-900/20'
                }`}>
                  {player.role}
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      </motion.div>
    </div>
  )
}

export function RevealScreen() {
  const players = useGameStore((s) => s.players)
  const setScreen = useGameStore((s) => s.setScreen)

  const playerList = Object.values(players)

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-6 relative overflow-y-auto">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-purple-900/40 via-background to-background -z-10" />

      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10 mt-10"
      >
        <h2 className="text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-purple-200 via-purple-400 to-indigo-400 drop-shadow-2xl mb-4">
          IDENTITY REVEAL
        </h2>
        <p className="text-white/50 text-sm tracking-[0.2em] uppercase">
          The truth behind the masks
        </p>
      </motion.div>

      <div className="w-full max-w-6xl grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-6 pb-20">
        {playerList.map((player, idx) => (
          <RevealCard key={player.name} player={player} index={idx} />
        ))}
        {/* Fill last slot with proceed button */}
        <div className="md:hidden lg:block lg:col-start-4 lg:row-start-2 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="text-center"
          >
            <Button
              onClick={() => setScreen('game_over')}
              className="w-full h-full aspect-[3/4] flex-col gap-4 bg-white/5 hover:bg-white/10 border-white/10"
              variant="ghost"
            >
              <ArrowRight className="w-8 h-8 text-white/50" />
              <span className="text-xs tracking-widest text-white/50">PROCEED TO RESULTS</span>
            </Button>
          </motion.div>
        </div>
      </div>

      <div className="fixed bottom-8 z-20 md:block hidden">
        <Button onClick={() => setScreen('game_over')} size="lg" className="shadow-[0_0_30px_rgba(255,255,255,0.1)]">
          View Game Results <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  )
}
