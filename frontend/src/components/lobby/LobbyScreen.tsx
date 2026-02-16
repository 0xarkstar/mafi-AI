import { motion } from 'framer-motion'
import { useGameStore } from '../../stores/gameStore'
import { PlayerSlot } from './PlayerSlot'
import { JoinForm } from './JoinForm'
import { AGENTS } from '../../lib/constants'

interface LobbyScreenProps {
  onJoin: (name: string) => void
}

export function LobbyScreen({ onJoin }: LobbyScreenProps) {
  const lobbyPlayers = useGameStore((s) => s.lobbyPlayers)
  const lobbyCount = useGameStore((s) => s.lobbyCount)
  const lobbyReady = useGameStore((s) => s.lobbyReady)
  const isPlayer = useGameStore((s) => s.isPlayer)
  const myPlayerName = useGameStore((s) => s.myPlayerName)

  return (
    <div className="h-full flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* Logo */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 200, damping: 20 }}
          className="text-center mb-12"
        >
          <h1
            className="text-6xl font-black tracking-tight text-transparent bg-clip-text mb-4 text-glow"
            style={{
              backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
            }}
          >
            MAFI-AI
          </h1>
          <div className="flex items-center justify-center gap-4 mb-4">
            {/* Progress bar */}
            <div className="w-64 h-2 bg-black/40 rounded-full overflow-hidden border border-white/10">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(lobbyCount / 7) * 100}%` }}
                className="h-full bg-gradient-to-r from-gold-dark to-gold"
              />
            </div>
            <span className="text-sm font-mono text-white/60">
              {lobbyCount}/7
            </span>
          </div>
          <p className="text-zinc-400 text-lg">
            {lobbyReady ? (
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="text-gold font-semibold"
              >
                Game starting soon...
              </motion.span>
            ) : (
              'Waiting for players to join'
            )}
          </p>
        </motion.div>

        {/* Player slots */}
        <motion.div
          variants={{
            show: {
              transition: {
                staggerChildren: 0.1,
              },
            },
          }}
          initial="hidden"
          animate="show"
          className="flex flex-wrap justify-center gap-4 mb-12"
        >
          {AGENTS.map((agent, i) => (
            <motion.div
              key={agent.name}
              variants={{
                hidden: { scale: 0, opacity: 0 },
                show: { scale: 1, opacity: 1 },
              }}
            >
              <PlayerSlot
                index={i}
                playerName={lobbyPlayers[i]}
                color={agent.color}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* Join form */}
        <div className="flex justify-center">
          <JoinForm
            onJoin={onJoin}
            isJoined={isPlayer}
            playerName={myPlayerName}
          />
        </div>
      </div>
    </div>
  )
}
