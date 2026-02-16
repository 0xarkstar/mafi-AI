import { motion, AnimatePresence } from 'framer-motion'
import { Skull, Target, Sword, Eye, Shield } from 'lucide-react'
import type { Player } from '../../lib/types'
import { AVATAR_IMAGES } from '../../lib/constants'
import { GlassCard } from '../ui/GlassCard'

interface PlayerCardProps {
  player: Player
  chatMessage?: string
  activeEmote?: string
  votesReceived?: number
  showVoteUI?: boolean
  onVote?: (name: string) => void
}

export function PlayerCard({
  player,
  chatMessage,
  activeEmote,
  votesReceived = 0,
  showVoteUI = false,
  onVote,
}: PlayerCardProps) {
  const { name, trait, isAlive, role, isSpeaking, avatarIndex } = player

  const canVote = showVoteUI && isAlive && onVote

  const roleConfig = {
    mafia: { color: 'bg-red-600', icon: Sword },
    detective: { color: 'bg-blue-600', icon: Eye },
    citizen: { color: 'bg-green-600', icon: Shield },
  }

  const RoleIcon = role ? roleConfig[role].icon : null
  const roleColor = role ? roleConfig[role].color : ''

  return (
    <motion.div
      layoutId={`player-${name}`}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 20 }}
    >
      <div className="relative w-full aspect-[4/5] group pointer-events-auto">
        {/* Chat Bubble Overlay - inside card, top area */}
        <AnimatePresence>
          {chatMessage && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="absolute top-1 left-1 right-1 z-[60] pointer-events-none"
            >
              <div className="bg-[#1e293b]/95 backdrop-blur-sm text-white text-[10px] p-2 rounded-lg border border-gold/40 shadow-lg">
                <p className="leading-snug line-clamp-3">{chatMessage}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Emote Overlay */}
        <AnimatePresence>
          {activeEmote && (
            <motion.div
              initial={{ scale: 0.5, y: 0 }}
              animate={{ y: -60, scale: 1.2 }}
              exit={{ y: -80, scale: 0.8, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="absolute top-0 right-0 z-[70]"
            >
              <div className="text-4xl filter drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]">
                {activeEmote}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Card */}
        <div
          className={`h-full ${canVote ? 'cursor-pointer' : ''}`}
          onClick={() => canVote && onVote(name)}
        >
          <GlassCard
            className={`w-full h-full rounded-xl overflow-hidden transition-all duration-300 ${
              isSpeaking && isAlive
                ? 'border-2 border-gold shadow-[0_0_25px_rgba(212,168,83,0.3)] scale-105'
                : ''
            } ${!isAlive ? 'opacity-60' : ''} ${
              canVote ? 'hover:border-red-500' : ''
            }`}
          >
          {/* Full card portrait image */}
          <img
            src={AVATAR_IMAGES[avatarIndex]}
            alt={name}
            className="absolute inset-0 w-full h-full object-cover"
          />

          {/* Bottom gradient */}
          <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/90 via-black/50 to-transparent z-10" />

          {/* Speaking border glow */}
          {isSpeaking && isAlive && (
            <div className="absolute inset-0 border-2 border-gold rounded-xl z-20 shadow-[inset_0_0_20px_rgba(212,168,83,0.2)] pointer-events-none" />
          )}

          {/* Vote hover overlay */}
          {canVote && (
            <div className="absolute inset-0 z-20 bg-red-600/0 group-hover:bg-red-600/20 transition-all duration-300 flex items-center justify-center">
              <Target className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
          )}

          {/* Vote count badge (top-right) */}
          {votesReceived > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-2 right-2 z-30 bg-red-600 text-white rounded-full px-2 py-1 text-xs font-bold shadow-lg"
            >
              {votesReceived}
            </motion.div>
          )}

          {/* Role badge (top-left) */}
          {role && RoleIcon && (
            <div className="absolute top-2 left-2 z-30">
              <div
                className={`${roleColor} rounded-full p-2 shadow-lg border-2 border-white/20`}
              >
                <RoleIcon className="w-4 h-4 text-white" />
              </div>
            </div>
          )}

          {/* Dead overlay */}
          {!isAlive && (
            <div className="absolute inset-0 z-20 bg-black/50 backdrop-blur-[2px] flex items-center justify-center">
              <Skull className="w-16 h-16 text-white/70" />
            </div>
          )}

          {/* Info section */}
          <div className="absolute bottom-0 left-0 right-0 z-20 text-center w-full p-3">
            <div className="font-bold text-sm text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
              {name}
            </div>
            <div className="text-[9px] text-white/60 uppercase tracking-widest drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
              {isAlive ? trait : 'ELIMINATED'}
            </div>
          </div>
        </GlassCard>
        </div>
      </div>
    </motion.div>
  )
}
