import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useGameStore } from '../store';
import { PlayerCard } from '../components/GameComponents';
import { ShieldAlert, Loader2 } from 'lucide-react';

export const LobbyScreen = () => {
  const { players, startGame } = useGameStore();

  // Simulate game start after delay
  useEffect(() => {
    if (players.length >= 7) {
        const timer = setTimeout(() => {
            startGame();
        }, 2000);
        return () => clearTimeout(timer);
    }
  }, [players, startGame]);

  const progressPercentage = (players.length / 7) * 100;

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-background to-background -z-10" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-5xl space-y-10 flex flex-col items-center"
      >
        <div className="text-center space-y-4 w-full max-w-lg">
            <h2 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-white/80 to-white/50 tracking-tight">GAME LOBBY</h2>

            {/* Progress Bar Section */}
            <div className="space-y-2">
                <div className="flex justify-between items-end px-1">
                    <div className="flex items-center gap-2 text-gold animate-pulse">
                         <ShieldAlert className="w-3 h-3" />
                         <span className="text-[10px] font-bold uppercase tracking-widest">Searching for Agents...</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-gold">{players.length}/7</span>
                </div>

                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden relative border border-white/10 shadow-inner">
                    {/* Active Bar */}
                    <motion.div
                        className="absolute top-0 left-0 h-full bg-gradient-to-r from-[#9a7a3a] via-[#d4a853] to-[#f0d78c] shadow-[0_0_20px_rgba(212,168,83,0.6)]"
                        initial={{ width: "14%" }}
                        animate={{ width: `${progressPercentage}%` }}
                        transition={{ duration: 0.5, ease: "circOut" }}
                    />

                    {/* Glow Tip */}
                    <motion.div
                        className="absolute top-0 bottom-0 w-1 bg-white blur-[2px] z-10"
                        initial={{ left: "14%" }}
                        animate={{ left: `${progressPercentage}%` }}
                        transition={{ duration: 0.5, ease: "circOut" }}
                    />
                </div>

                <div className="text-right">
                    <span className="text-[9px] font-mono text-white/30 tracking-widest">
                        {players.length === 7 ? "CONNECTION ESTABLISHED" : "ESTABLISHING UPLINK..."}
                    </span>
                </div>
            </div>
        </div>

        {/* Players Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 w-full">
            {/* Render actual players */}
            {players.map((p) => (
                <motion.div
                    key={p.id}
                    initial={{ opacity: 0, scale: 0.5, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ type: "spring", bounce: 0.4 }}
                    className="w-full aspect-[3/4]"
                >
                    <PlayerCard player={p} />
                </motion.div>
            ))}

            {/* Render empty slots */}
            {[...Array(7 - players.length)].map((_, i) => (
                 <motion.div
                    key={`empty-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="w-full aspect-[3/4] rounded-xl border-2 border-dashed border-white/5 flex flex-col items-center justify-center gap-2 bg-white/[0.02]"
                 >
                    <Loader2 className="w-6 h-6 text-white/10 animate-spin" />
                    <span className="text-[9px] uppercase font-bold text-white/20 tracking-widest">Scanning</span>
                </motion.div>
            ))}
        </div>

        {/* Status Message */}
        <div className="h-8 flex items-center justify-center">
             {players.length === 7 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="px-6 py-2 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-bold uppercase tracking-[0.2em] flex items-center gap-2"
                >
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    Match Found • Initializing Game...
                </motion.div>
            )}
        </div>
      </motion.div>
    </div>
  );
};
