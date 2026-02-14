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
          <h1 className="text-6xl font-bold mb-4">
            <span className="text-5xl mr-2">🎭</span>
            <span className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
              MAFIA AI
            </span>
          </h1>
          <p className="text-zinc-400 text-lg">
            {lobbyReady ? (
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="text-emerald-400 font-semibold"
              >
                Game starting soon...
              </motion.span>
            ) : (
              `Waiting for players ${lobbyCount}/7`
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
