import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Target } from 'lucide-react';
import { ActionRequest } from '../types';

interface NightActionPanelProps {
  show: boolean;
  currentAction: ActionRequest | null;
  timeLeft: number;
  onAction: (targetName: string) => void;
}

export const NightActionPanel = ({ show, currentAction, timeLeft, onAction }: NightActionPanelProps) => (
  <AnimatePresence>
    {show && currentAction && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 z-[80] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="flex flex-col items-center gap-6 text-center max-w-md px-6"
        >
          <AlertCircle className="w-12 h-12 text-indigo-400" />
          <h3 className="text-2xl font-bold text-white">{currentAction.prompt}</h3>
          <div className="flex flex-wrap gap-3 justify-center">
            {currentAction.options.map((name) => (
              <motion.button
                key={name}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => onAction(name)}
                className="px-6 py-3 bg-indigo-500/20 border border-indigo-500/50 rounded-xl text-indigo-300 font-bold hover:bg-indigo-500/30 transition-colors"
              >
                <Target className="w-4 h-4 inline mr-2" />
                {name}
              </motion.button>
            ))}
          </div>
          <div className={`text-sm font-mono ${timeLeft <= 10 ? 'text-red-400 animate-pulse' : 'text-white/40'}`}>
            {timeLeft}s remaining
          </div>
        </motion.div>
      </motion.div>
    )}
  </AnimatePresence>
);
