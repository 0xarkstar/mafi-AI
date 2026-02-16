import { motion } from 'framer-motion'
import { AVATAR_IMAGES } from '../../lib/constants'

interface PlayerSlotProps {
  index: number
  playerName?: string
  color?: string
}

export function PlayerSlot({ index, playerName, color }: PlayerSlotProps) {
  const isEmpty = !playerName

  return (
    <div className="flex flex-col items-center gap-2">
      <motion.div
        className={`
          w-20 h-20 rounded-full flex items-center justify-center overflow-hidden
          ${
            isEmpty
              ? 'border-2 border-dashed border-zinc-600 bg-zinc-900/50'
              : 'border-2 border-solid bg-zinc-800/80'
          }
        `}
        style={isEmpty ? {} : { borderColor: color || '#D4A853' }}
        animate={
          isEmpty
            ? {
                scale: [1, 1.05, 1],
                opacity: [0.5, 0.7, 0.5],
              }
            : {}
        }
        transition={
          isEmpty
            ? {
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }
            : {}
        }
      >
        {isEmpty ? (
          <span className="text-zinc-500 text-sm font-mono">{index + 1}</span>
        ) : (
          <motion.img
            src={AVATAR_IMAGES[index]}
            alt={playerName}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            className="w-full h-full object-cover"
          />
        )}
      </motion.div>

      <div className="text-center">
        {isEmpty ? (
          <span className="text-xs text-zinc-500">Empty</span>
        ) : (
          <motion.span
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm font-semibold"
            style={{ color: color || '#D4A853' }}
          >
            {playerName}
          </motion.span>
        )}
      </div>
    </div>
  )
}
