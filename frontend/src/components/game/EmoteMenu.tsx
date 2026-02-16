import { motion, AnimatePresence } from 'framer-motion'

interface EmoteMenuProps {
  isOpen: boolean
  onSelect: (emote: string) => void
  onClose: () => void
}

const EMOTES = ['👍', '👎', '😂', '😡', '🤔', '😱', '👻', '💀']

export function EmoteMenu({ isOpen, onSelect, onClose }: EmoteMenuProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={onClose} />

          {/* Menu */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-full left-0 mb-2 z-50 bg-[#1e293b]/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl w-64 grid grid-cols-4 gap-2"
          >
            {EMOTES.map((emoji) => (
              <button
                key={emoji}
                onClick={() => {
                  onSelect(emoji)
                  onClose()
                }}
                className="w-12 h-12 flex items-center justify-center text-2xl hover:bg-white/10 rounded-xl transition-colors active:scale-95"
              >
                {emoji}
              </button>
            ))}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
