import { useState } from 'react'
import { motion } from 'framer-motion'
import { useGameStore } from '../stores/gameStore'
import { useChatStore } from '../stores/chatStore'
import { useBettingStore } from '../stores/bettingStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { MessageSquare, TrendingUp, X } from 'lucide-react'
import { AVATAR_IMAGES } from '../lib/constants'
import { BettingPanel } from '../components/betting/BettingPanel'

export function SpectatorScreen() {
  useWebSocket() // Connect to real game events

  const players = useGameStore((s) => s.players)
  const phase = useGameStore((s) => s.phase)
  const round = useGameStore((s) => s.round)
  const messages = useChatStore((s) => s.messages)
  const odds = useBettingStore((s) => s.odds)

  const [showChat, setShowChat] = useState(false)

  const playerList = Object.values(players)

  return (
    <div className="h-screen w-full flex flex-col bg-gradient-to-br from-zinc-950 to-zinc-900 relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-purple-900/5 rounded-full blur-[150px]" />
        <div className="absolute bottom-[-15%] right-[-10%] w-[50%] h-[50%] bg-gold/5 rounded-full blur-[100px]" />
      </div>

      {/* Header */}
      <div className="relative z-10 p-6 border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1
              className="text-3xl font-black tracking-tight text-transparent bg-clip-text text-glow"
              style={{
                backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
              }}
            >
              MAFI-AI
            </h1>
            <p className="text-sm text-white/40 uppercase tracking-widest mt-1">
              Spectator Mode
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs text-white/40 uppercase tracking-wider">Phase</div>
              <div className="text-sm font-bold text-white">
                {phase.replace('_', ' ')} - Round {round}
              </div>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowChat(!showChat)}
              icon={showChat ? <X className="w-4 h-4" /> : <MessageSquare className="w-4 h-4" />}
            >
              {showChat ? 'Hide Chat' : 'Show Chat'}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 relative z-10 overflow-hidden">
        <div className="max-w-7xl mx-auto h-full flex gap-6 p-6">
          {/* Left: Game Board */}
          <div className="flex-1 flex flex-col gap-6">
            {/* Player Grid */}
            <GlassCard className="flex-1 p-6">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>Players</span>
                <span className="text-sm text-white/40">
                  ({playerList.filter((p) => p.isAlive).length} alive)
                </span>
              </h2>
              <div className="grid grid-cols-4 gap-4">
                {playerList.map((player) => (
                  <motion.div
                    key={player.name}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className={`relative aspect-[3/4] rounded-lg overflow-hidden border-2 ${
                      player.isAlive
                        ? 'border-white/10'
                        : 'border-red-900/30 grayscale opacity-50'
                    }`}
                  >
                    {/* Avatar */}
                    <img
                      src={AVATAR_IMAGES[player.avatarIndex]}
                      alt={player.name}
                      className="w-full h-full object-cover"
                    />

                    {/* Bottom info */}
                    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-3">
                      <div className="text-center">
                        <div className="text-sm font-bold text-white truncate">
                          {player.name}
                        </div>
                        <div className="text-xs text-white/40 uppercase tracking-widest">
                          {player.isAlive ? player.trait : 'Eliminated'}
                        </div>
                      </div>
                    </div>

                    {/* Speaking indicator */}
                    {player.isSpeaking && player.isAlive && (
                      <div className="absolute inset-0 border-2 border-gold shadow-[0_0_20px_rgba(212,168,83,0.4)]" />
                    )}
                  </motion.div>
                ))}
              </div>
            </GlassCard>

            {/* Odds Display */}
            <GlassCard className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-gold" />
                  <span className="text-sm font-bold text-white">Live Odds</span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400 font-mono">
                      {(odds.mafiaWinProb * 100).toFixed(0)}%
                    </span>
                    <span className="text-white/40">Mafia</span>
                  </div>
                  <div className="w-px h-4 bg-white/10" />
                  <div className="flex items-center gap-2">
                    <span className="text-white/40">Citizens</span>
                    <span className="text-green-400 font-mono">
                      {(odds.citizenWinProb * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
              {/* Progress bar */}
              <div className="mt-3 h-2 bg-black/40 rounded-full overflow-hidden border border-white/10">
                <motion.div
                  initial={{ width: `${odds.mafiaWinProb * 100}%` }}
                  animate={{ width: `${odds.mafiaWinProb * 100}%` }}
                  transition={{ duration: 0.5 }}
                  className="h-full bg-gradient-to-r from-red-800 to-red-500"
                />
              </div>
            </GlassCard>
          </div>

          {/* Right: Betting & Chat */}
          <div className="w-[400px] flex flex-col gap-4">
            {/* Betting Panel */}
            <div className="flex-1 overflow-y-auto">
              <BettingPanel />
            </div>

            {/* Chat (conditional) */}
            {showChat && (
              <GlassCard className="h-[300px] flex flex-col p-4">
                <h3 className="text-sm font-bold text-white mb-3">Game Chat</h3>
                <div className="flex-1 overflow-y-auto space-y-2 text-sm">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`p-2 rounded ${
                        msg.type === 'system'
                          ? 'bg-white/5 text-white/60 italic'
                          : 'bg-zinc-800/50 text-white'
                      }`}
                    >
                      {msg.type === 'agent' && (
                        <div className="font-bold text-xs text-gold mb-1">{msg.agent}</div>
                      )}
                      <div>{msg.message}</div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      </div>

      {/* Market Feed Ticker (bottom) */}
      <div className="relative z-10 h-8 bg-black/40 border-t border-white/10 overflow-hidden">
        <div className="flex items-center h-full px-4">
          <span className="text-xs text-white/40 uppercase tracking-wider mr-4">
            Live Market Feed
          </span>
          <div className="flex-1 overflow-hidden">
            <motion.div
              className="flex gap-8 text-xs text-white/60"
              animate={{ x: [0, -1000] }}
              transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
            >
              <span>🔥 Betting window open for Round {round}</span>
              <span>📊 Total pool: Updating...</span>
              <span>👥 {playerList.filter((p) => p.isAlive).length} players remaining</span>
              <span>⚡ Phase: {phase.replace('_', ' ')}</span>
              <span>🎲 Odds updating in real-time</span>
              {/* Repeat for seamless loop */}
              <span>🔥 Betting window open for Round {round}</span>
              <span>📊 Total pool: Updating...</span>
              <span>👥 {playerList.filter((p) => p.isAlive).length} players remaining</span>
              <span>⚡ Phase: {phase.replace('_', ' ')}</span>
              <span>🎲 Odds updating in real-time</span>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
