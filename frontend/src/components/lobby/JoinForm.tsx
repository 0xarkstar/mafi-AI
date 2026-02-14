import { useState } from 'react'
import { motion } from 'framer-motion'
import { Check } from 'lucide-react'
import { GlassCard } from '../ui/GlassCard'
import { Button } from '../ui/Button'

interface JoinFormProps {
  onJoin: (name: string) => void
  isJoined: boolean
  playerName: string | null
}

export function JoinForm({ onJoin, isJoined, playerName }: JoinFormProps) {
  const [name, setName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim() && !isJoined) {
      onJoin(name.trim())
    }
  }

  if (isJoined && playerName) {
    return (
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
      >
        <GlassCard className="px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <Check className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="text-sm text-zinc-400">Joined as</div>
              <div className="text-lg font-semibold text-emerald-400">{playerName}</div>
            </div>
          </div>
        </GlassCard>
      </motion.div>
    )
  }

  return (
    <GlassCard className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="p-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-zinc-300 mb-2">
              Enter your name
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              className="w-full px-4 py-3 rounded-lg glass-card text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              maxLength={20}
              autoFocus
            />
          </div>

          <Button type="submit" variant="primary" size="lg" className="w-full" disabled={!name.trim()}>
            Join Game
          </Button>
        </div>
      </form>
    </GlassCard>
  )
}
