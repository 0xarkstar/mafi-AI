import { Gamepad2, MessageSquare, DollarSign } from 'lucide-react'
import { motion } from 'framer-motion'

type MobileTab = 'game' | 'chat' | 'bet'

interface MobileTabBarProps {
  activeTab: MobileTab
  onTabChange: (tab: MobileTab) => void
}

const tabs: { id: MobileTab; label: string; icon: typeof Gamepad2 }[] = [
  { id: 'game', label: 'Game', icon: Gamepad2 },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'bet', label: 'Bet', icon: DollarSign },
]

export function MobileTabBar({ activeTab, onTabChange }: MobileTabBarProps) {
  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40">
      <div className="glass-card border-t border-white/10 rounded-none">
        <div className="grid grid-cols-3">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className="relative flex flex-col items-center gap-1 py-3 transition-colors duration-200"
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute inset-0 bg-emerald-500/10"
                    transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                  />
                )}

                <Icon
                  className={`w-5 h-5 relative z-10 transition-colors ${
                    isActive ? 'text-emerald-400' : 'text-zinc-400'
                  }`}
                />
                <span
                  className={`text-xs relative z-10 transition-colors ${
                    isActive ? 'text-emerald-400 font-semibold' : 'text-zinc-400'
                  }`}
                >
                  {tab.label}
                </span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
