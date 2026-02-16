import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Header } from './Header'
import { MobileTabBar } from './MobileTabBar'
import { GameBoard } from '../game/GameBoard'
import { ChatPanel } from '../game/ChatPanel'
import { BettingPanel } from '../betting/BettingPanel'
import { BettingStatusBar } from '../game/BettingStatusBar'
import { NightOverlay } from '../game/NightOverlay'
import { useGameStore } from '../../stores/gameStore'

type MobileTab = 'game' | 'chat' | 'bet'

export function GameLayout() {
  const [activeTab, setActiveTab] = useState<MobileTab>('game')
  const phase = useGameStore((s) => s.phase)

  return (
    <div className="h-full flex flex-col relative overflow-hidden">
      {/* Day/Night background crossfade */}
      <img
        src="/images/game-bg.png"
        alt=""
        className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${
          phase === 'night' ? 'opacity-0' : 'opacity-100'
        }`}
      />
      <img
        src="/images/game-bg-night.png"
        alt=""
        className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${
          phase === 'night' ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* Phase-tinted overlay */}
      <div
        className={`absolute inset-0 transition-all duration-[2000ms] z-[1] pointer-events-none ${
          phase === 'night'
            ? 'bg-[#0a0e1f]/60'
            : phase === 'day_vote'
              ? 'bg-[#1a0505]/70'
              : 'bg-[#0a0a05]/50'
        }`}
      />

      {/* Night overlay (full screen) */}
      <NightOverlay isVisible={phase === 'night'} />

      {/* Everything below needs relative z-10 to appear above backgrounds */}
      <div className="relative z-10 flex flex-col flex-1 overflow-hidden">
        <Header />

      {/* Desktop Layout (3 columns) */}
      <div className="hidden lg:grid lg:grid-cols-[280px_1fr_320px] gap-4 p-4 flex-1 overflow-hidden relative">
        {/* Left: Player cards sidebar */}
        <div className="overflow-y-auto">
          <GameBoard />
        </div>

        {/* Center: Chat + action panel */}
        <div className="flex flex-col min-h-0">
          <ChatPanel />
        </div>

        {/* Right: Betting panel */}
        <div className="overflow-y-auto space-y-4">
          <BettingPanel />
        </div>

        {/* Betting Status Bar (bottom center overlay) */}
        <BettingStatusBar />
      </div>

      {/* Mobile Layout (single column with tabs) */}
      <div className="lg:hidden flex-1 flex flex-col overflow-hidden pb-16">
        <AnimatePresence mode="wait">
          {activeTab === 'game' && (
            <motion.div
              key="game"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex-1 overflow-y-auto p-4"
            >
              <GameBoard />
            </motion.div>
          )}

          {activeTab === 'chat' && (
            <motion.div
              key="chat"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex-1 flex flex-col min-h-0 p-4"
            >
              <ChatPanel />
            </motion.div>
          )}

          {activeTab === 'bet' && (
            <motion.div
              key="bet"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex-1 overflow-y-auto p-4 space-y-4"
            >
              <div className="glass-card p-4 text-center text-zinc-500">
                Betting panel loading...
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <MobileTabBar activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
    </div>
  )
}
