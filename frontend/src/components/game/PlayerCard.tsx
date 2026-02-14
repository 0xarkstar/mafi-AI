import { motion } from 'framer-motion'
import { Skull } from 'lucide-react'
import type { Player } from '../../lib/types'
import { Badge } from '../ui/Badge'
import { PlayerAvatar } from './PlayerAvatar'

interface PlayerCardProps {
  player: Player
}

export function PlayerCard({ player }: PlayerCardProps) {
  const { name, color, trait, isAlive, role, isSpeaking } = player

  return (
    <motion.div
      layoutId={`player-${name}`}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
    >
      <div
        className={`glass-card p-4 relative ${
          isSpeaking ? 'ring-2 ring-offset-2 ring-offset-transparent animate-pulse-glow' : ''
        } ${!isAlive ? 'opacity-50 grayscale' : ''}`}
        style={isSpeaking ? { ['--tw-ring-color' as string]: color } : {}}
      >
        {/* Avatar */}
        <div className="flex justify-center mb-3">
          <PlayerAvatar name={name} color={color} isAlive={isAlive} size={64} />
        </div>

        {/* Name */}
        <div className="text-center mb-2">
          <h3 className="font-semibold text-sm truncate" style={{ color }}>
            {name}
          </h3>
        </div>

        {/* Trait badge */}
        <div className="flex justify-center mb-2">
          <span className="text-xs text-zinc-500 bg-zinc-800/50 px-2 py-0.5 rounded-full">
            {trait}
          </span>
        </div>

        {/* Status */}
        <div className="flex justify-center gap-2 flex-wrap">
          {!isAlive && (
            <Badge variant="dead">
              <Skull className="w-3 h-3" />
              Dead
            </Badge>
          )}

          {isAlive && isSpeaking && <Badge variant="speaking">Speaking</Badge>}

          {role && <Badge variant={role}>{role.toUpperCase()}</Badge>}
        </div>
      </div>
    </motion.div>
  )
}
