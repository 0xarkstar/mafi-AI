import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useGameStore } from '../stores/gameStore'
import { useChatStore } from '../stores/chatStore'
import { useBettingStore } from '../stores/bettingStore'
import { useWebSocket } from '../hooks/useWebSocket'
import { GlassCard } from '../components/ui/GlassCard'
import { Button } from '../components/ui/Button'
import { MessageSquare, TrendingUp, X } from 'lucide-react'
import { AVATAR_IMAGES } from '../lib/constants'
import type { BetType, Bet } from '../lib/types'

export function SpectatorScreen() {
  useWebSocket() // Connect to real game events

  const players = useGameStore((s) => s.players)
  const phase = useGameStore((s) => s.phase)
  const round = useGameStore((s) => s.round)
  const messages = useChatStore((s) => s.messages)
  const odds = useBettingStore((s) => s.odds)
  const bets = useBettingStore((s) => s.bets)
  const balance = useBettingStore((s) => s.balance)
  const addBet = useBettingStore((s) => s.addBet)
  const setBalance = useBettingStore((s) => s.setBalance)

  const [showChat, setShowChat] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [lastReadCount, setLastReadCount] = useState(0)

  // Betting terminal state
  const [betType, setBetType] = useState<BetType>('side_win')
  const [target, setTarget] = useState<string>('Mafia')
  const [amount, setAmount] = useState<number>(10)

  const playerList = Object.values(players)

  // Track unread when chat is closed
  useEffect(() => {
    if (!showChat) {
      setUnreadCount(messages.length - lastReadCount)
    }
  }, [messages.length, showChat, lastReadCount])

  // Mark as read when chat opens
  useEffect(() => {
    if (showChat) {
      setUnreadCount(0)
      setLastReadCount(messages.length)
    }
  }, [showChat, messages.length])

  // Calculate targets based on bet type
  const targets =
    betType === 'side_win'
      ? ['Mafia', 'Citizens']
      : playerList
          .filter((p) => betType !== 'next_elimination' || p.isAlive)
          .map((p) => p.name)

  // Reset target when bet type changes
  useEffect(() => {
    if (targets.length > 0 && !targets.includes(target)) {
      const firstTarget = targets[0]
      if (firstTarget) {
        setTarget(firstTarget)
      }
    }
  }, [betType, targets, target])

  // Calculate probability based on bet type and target
  const probability =
    betType === 'side_win'
      ? target === 'Mafia'
        ? odds.mafiaWinProb
        : odds.citizenWinProb
      : odds.mafiaSuspects[target] || 0.5

  // Calculate potential payout
  const potentialPayout = probability > 0 ? amount * (1 / probability) : 0

  // Handle place bet
  const handlePlaceBet = async () => {
    if (!amount || amount > balance) return

    const newBet: Bet = {
      id: `bet-${Date.now()}`,
      betType,
      target,
      amount,
      status: 'pending',
      weight: round === 0 ? 1.5 : round === 1 ? 1.2 : 1.0,
    }

    addBet(newBet)
    setBalance(balance - amount)

    // Send to server
    try {
      await fetch('/api/bets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: 'current',
          bet_type: betType,
          target,
          amount,
          round_number: round,
        }),
      })
    } catch {
      // Bet is tracked locally regardless
    }
  }

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
              {!showChat && unreadCount > 0 && (
                <span className="ml-1 bg-purple-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  {unreadCount}
                </span>
              )}
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

            {/* Game Log */}
            <GlassCard className="p-4 max-h-[200px] overflow-y-auto">
              <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Game Log</h3>
              <div className="space-y-1">
                {messages.slice(-15).map((msg) => (
                  <div
                    key={msg.id}
                    className={`text-xs py-1 ${
                      msg.type === 'elimination'
                        ? 'text-red-400'
                        : msg.type === 'game-over'
                          ? 'text-emerald-400'
                          : msg.type === 'system'
                            ? 'text-white/40 italic'
                            : 'text-white/70'
                    }`}
                  >
                    {msg.type === 'agent' && (
                      <span className="text-gold font-bold">{msg.agent}: </span>
                    )}
                    {msg.message}
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          {/* Right: Betting Terminal */}
          <div className="w-[400px] flex flex-col">
            {/* Betting Terminal */}
            <GlassCard className="flex-1 p-6 space-y-5 overflow-y-auto border-gold/20">
              <h2 className="text-lg font-bold text-gold tracking-wider flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                BETTING TERMINAL
              </h2>

              {/* Bet Type Selector */}
              <div className="space-y-2">
                <label className="text-xs text-white/40 uppercase tracking-wider">Bet Type</label>
                <select
                  value={betType}
                  onChange={(e) => setBetType(e.target.value as BetType)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-gold/50 outline-none"
                >
                  <option value="side_win">Side Win</option>
                  <option value="next_elimination">Next Elimination</option>
                  <option value="is_mafia">Is Mafia</option>
                  <option value="is_ai_or_human">AI or Human</option>
                </select>
              </div>

              {/* Target Selector */}
              <div className="space-y-2">
                <label className="text-xs text-white/40 uppercase tracking-wider">Target</label>
                <select
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-gold/50 outline-none"
                >
                  {targets.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount Input */}
              <div className="space-y-2">
                <label className="text-xs text-white/40 uppercase tracking-wider">Amount</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gold font-mono">
                    $
                  </span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => {
                      const val = Number(e.target.value)
                      if (!isNaN(val) && val >= 0) setAmount(val)
                    }}
                    className="w-full bg-black/40 border border-white/10 rounded-lg pl-7 pr-3 py-2 text-sm text-white font-mono focus:border-gold/50 outline-none"
                  />
                </div>
                {/* Quick amounts */}
                <div className="flex gap-2 flex-wrap">
                  {[1, 5, 10, 25].map((amt) => (
                    <button
                      key={amt}
                      onClick={() => setAmount(amt)}
                      className="px-3 py-1 text-xs font-mono border border-gold/30 rounded-full text-gold hover:bg-gold/10 transition-colors"
                    >
                      ${amt}
                    </button>
                  ))}
                  <button
                    onClick={() => setAmount(balance)}
                    className="px-3 py-1 text-xs font-mono border border-gold/30 rounded-full text-gold hover:bg-gold/10 transition-colors font-bold"
                  >
                    MAX
                  </button>
                </div>
              </div>

              {/* Payout Calculator */}
              <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-1">
                <div className="flex justify-between text-xs text-white/40">
                  <span>Probability</span>
                  <span className="font-mono">{(probability * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-sm text-gold font-bold">
                  <span>Potential Payout</span>
                  <span className="font-mono">${potentialPayout.toFixed(2)}</span>
                </div>
              </div>

              {/* Place Bet Button */}
              <button
                onClick={handlePlaceBet}
                disabled={!amount || amount > balance}
                className="w-full py-3 font-bold text-sm uppercase tracking-wider rounded-lg bg-gradient-to-r from-[#9a7a3a] to-[#D4A853] hover:from-[#D4A853] hover:to-[#f0d78c] text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
              >
                Place Bet — ${amount}
              </button>

              {/* Balance display */}
              <div className="text-center text-xs text-white/40">
                Balance: <span className="text-gold font-mono">${balance}</span>
              </div>

              {/* My Bets */}
              <div className="space-y-2 border-t border-white/10 pt-4">
                <h3 className="text-xs text-white/40 uppercase tracking-wider">My Bets</h3>
                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {bets.map((bet) => (
                    <div
                      key={bet.id}
                      className="bg-black/30 border border-white/5 rounded-lg p-3 flex justify-between items-center"
                    >
                      <div>
                        <div className="text-xs text-white">
                          {bet.betType.replace(/_/g, ' ')} → {bet.target}
                        </div>
                        <div className="text-xs text-white/40 font-mono">${bet.amount}</div>
                      </div>
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          bet.status === 'pending'
                            ? 'bg-yellow-900/40 text-yellow-400'
                            : bet.status === 'won'
                              ? 'bg-green-900/40 text-green-400'
                              : 'bg-red-900/40 text-red-400'
                        }`}
                      >
                        {bet.status}
                      </span>
                    </div>
                  ))}
                  {bets.length === 0 && (
                    <p className="text-xs text-white/20 italic text-center">
                      No bets placed yet
                    </p>
                  )}
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>

      {/* Spectator Chat (floating) */}
      <AnimatePresence>
        {showChat && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="absolute bottom-16 right-6 w-[340px] h-[420px] z-50"
          >
            <GlassCard className="h-full flex flex-col p-4 border-purple-500/20">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-purple-300 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Spectator Chat
                </h3>
                <span className="text-xs text-white/30">👥 watching</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2 text-sm">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`p-2 rounded ${
                      msg.type === 'system'
                        ? 'bg-white/5 text-white/60 italic'
                        : msg.type === 'elimination'
                          ? 'bg-red-900/20 text-red-300'
                          : msg.type === 'game-over'
                            ? 'bg-emerald-900/20 text-emerald-300'
                            : 'bg-zinc-800/50 text-white'
                    }`}
                  >
                    {msg.type === 'agent' && (
                      <div className="font-bold text-xs text-gold mb-1">{msg.agent}</div>
                    )}
                    <div className="text-xs">{msg.message}</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

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
