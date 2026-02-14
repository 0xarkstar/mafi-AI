import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Header } from './Header'
import { MobileTabBar } from './MobileTabBar'
import { GameBoard } from '../game/GameBoard'
import { ChatPanel } from '../game/ChatPanel'
import { BettingPanel } from '../betting/BettingPanel'

type MobileTab = 'game' | 'chat' | 'bet'

export function GameLayout() {
  const [activeTab, setActiveTab] = useState<MobileTab>('game')

  return (
    <div className="h-full flex flex-col">
      <Header />

      {/* Desktop Layout (3 columns) */}
      <div className="hidden lg:grid lg:grid-cols-[280px_1fr_320px] gap-4 p-4 flex-1 overflow-hidden">
        {/* Left: Player cards sidebar */}
        <div className="overflow-y-auto">
          <GameBoard />
        </div>

        {/* Center: Chat + action panel */}
        <div className="flex flex-col min-h-0">
          <ChatPanel />
        </div>

        {/* Right: Betting panel (placeholder for p-impl-bet) */}
        <div className="overflow-y-auto space-y-4">
          <BettingPanel />
        </div>
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
  )
}
