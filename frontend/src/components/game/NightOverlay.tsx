import { motion, AnimatePresence } from 'framer-motion'
import { Moon } from 'lucide-react'

interface NightOverlayProps {
  isVisible: boolean
}

export function NightOverlay({ isVisible }: NightOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-50 flex items-center justify-center bg-black text-center"
        >
          <div className="space-y-6 relative">
            <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full" />
            <motion.div
              animate={{ rotate: 360, scale: [1, 1.1, 1] }}
              transition={{ duration: 3, ease: 'circOut' }}
              className="relative z-10"
            >
              <Moon className="w-32 h-32 text-indigo-400 drop-shadow-[0_0_50px_rgba(129,140,248,0.5)]" />
            </motion.div>
            <motion.h2
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="text-5xl font-extrabold text-white tracking-[0.3em] relative z-10"
            >
              NIGHT PHASE
            </motion.h2>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
