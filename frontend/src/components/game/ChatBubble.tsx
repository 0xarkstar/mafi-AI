import { motion } from 'framer-motion'
import { Skull, Trophy } from 'lucide-react'
import type { ChatMessage } from '../../lib/types'
import { AGENTS } from '../../lib/constants'

interface ChatBubbleProps {
  message: ChatMessage
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const { agent, message: text, type } = message

  // Find agent color
  const agentData = AGENTS.find((a) => a.name === agent)
  const agentColor = agentData?.color || '#71717a'

  // System messages (centered, muted)
  if (type === 'system') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <p className="text-sm text-zinc-500 italic">{text}</p>
      </motion.div>
    )
  }

  // Elimination messages (centered, red tint)
  if (type === 'elimination') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-red-950/30 border border-red-500/30 rounded-lg">
          <Skull className="w-4 h-4 text-red-400" />
          <p className="text-sm text-red-300">{text}</p>
        </div>
      </motion.div>
    )
  }

  // Game over messages (centered, green/gold)
  if (type === 'game-over') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-950/30 border border-emerald-500/30 rounded-lg">
          <Trophy className="w-4 h-4 text-emerald-400" />
          <p className="text-sm text-emerald-300 font-semibold">{text}</p>
        </div>
      </motion.div>
    )
  }

  // Agent messages (left-aligned, colored border)
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex flex-col gap-1"
    >
      <div className="flex items-baseline gap-2">
        <span className="text-xs font-semibold" style={{ color: agentColor }}>
          {agent}
        </span>
        <span className="text-xs text-zinc-600">
          {new Date(message.timestamp).toLocaleTimeString()}
        </span>
      </div>
      <div
        className="px-3 py-2 rounded-lg bg-zinc-900/50 border-l-2"
        style={{ borderLeftColor: agentColor }}
      >
        <p className="text-sm text-zinc-200">{text}</p>
      </div>
    </motion.div>
  )
}
