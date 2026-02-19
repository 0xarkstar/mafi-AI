import type React from 'react';
import { Player } from '../types';
import { AVATAR_IMAGES } from '../constants';
import { GlassCard } from './UIComponents';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Diamond, Moon, Flame, Eye, Hexagon, Zap, Star, TrendingUp } from 'lucide-react';
import { useGameStore } from '../store';

// --- Icon Helper ---
const AvatarIcon = ({ name, className }: { name: string; className?: string }) => {
  const icons: Record<string, React.ElementType> = {
    User, Diamond, Moon, Flame, Eye, Hash: Hexagon, Zap, Star
  };
  const Icon = icons[name] || User;
  return <Icon className={className} />;
};

// --- Player Card (Lobby/Grid) ---
export const PlayerCard = ({ player }: { player: Player }) => {
    return (
        <div className="relative group w-full h-full">
             <GlassCard className="w-full h-full flex flex-col items-end justify-end p-0 bg-[#0f172a]/60 border-white/5 hover:border-gold/30 transition-all duration-300 overflow-hidden relative">
                {/* Full card avatar image */}
                {player.avatarIndex != null ? (
                  <img src={AVATAR_IMAGES[player.avatarIndex]} alt={player.name} className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-white/5 to-black/40">
                    <AvatarIcon name={player.avatarIcon} className="w-16 h-16 text-white/30 group-hover:text-gold/50 transition-colors" />
                  </div>
                )}

                {/* Bottom gradient overlay */}
                <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/90 via-black/50 to-transparent z-10" />

                {/* Info */}
                <div className="relative z-20 w-full p-3 flex flex-col items-center gap-1.5">
                    <span className="font-bold text-sm text-white tracking-wide group-hover:text-gold transition-colors drop-shadow-lg">{player.name}</span>
                    <span className="text-[9px] text-white/40 uppercase tracking-widest font-bold">{player.trait}</span>
                </div>
             </GlassCard>
        </div>
    );
};

// --- Betting Status Bar (Bottom Overlay) ---
export const BettingStatusBar = () => {
    const { odds } = useGameStore();
    const mafiaProb = odds?.mafiaWinProb ?? 0.35;
    const mafiaOdds = odds ? (1 / odds.mafiaWinProb).toFixed(2) : '—';
    const citizenOdds = odds ? (1 / odds.citizenWinProb).toFixed(2) : '—';
    const mafiaWidth = `${(mafiaProb * 100).toFixed(0)}%`;

    return (
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex items-center gap-6 bg-[#0f172a]/60 backdrop-blur-md border border-white/10 px-8 py-3 rounded-full shadow-[0_0_30px_rgba(0,0,0,0.3)] hover:bg-[#0f172a]/80 transition-colors duration-300">
             {/* Left Stats */}
             <div className="flex flex-col items-end min-w-[80px]">
                 <div className="flex items-center gap-1.5 text-red-500">
                    <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Mafia</span>
                    <TrendingUp className="w-3 h-3" />
                 </div>
                 <span className="text-xs font-mono font-bold text-white tracking-tight">{mafiaOdds}x</span>
             </div>

             {/* Bar */}
             <div className="h-1.5 w-[300px] bg-black/50 rounded-full overflow-hidden flex relative border border-white/10 shadow-inner">
                 <motion.div
                    animate={{ width: mafiaWidth }}
                    transition={{ duration: 1, ease: "easeInOut" }}
                    className="h-full bg-gradient-to-r from-red-800 to-red-500 shadow-[0_0_10px_rgba(239,68,68,0.4)]"
                 />
                 <div className="flex-1 bg-gradient-to-l from-green-800 to-green-500 shadow-[0_0_10px_rgba(34,197,94,0.4)]" />

                 {/* Ticks */}
                 <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-white/20 z-10" />
             </div>

             {/* Right Stats */}
              <div className="flex flex-col items-start min-w-[80px]">
                 <div className="flex items-center gap-1.5 text-green-500">
                    <TrendingUp className="w-3 h-3" />
                    <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">Citizens</span>
                 </div>
                 <span className="text-xs font-mono font-bold text-white tracking-tight">{citizenOdds}x</span>
             </div>
        </div>
    );
};

// --- Emote Menu ---
export const EmoteMenu = ({ onSelect, isOpen, onClose }: { onSelect: (emote: string) => void; isOpen: boolean; onClose: () => void }) => {
    const emotes = ["👍", "👎", "😂", "😡", "🤔", "😱", "👻", "💀"];

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    <div className="fixed inset-0 z-40" onClick={onClose} />
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 10 }}
                        className="absolute bottom-full left-0 mb-2 z-50 bg-[#1e293b]/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl w-64 grid grid-cols-4 gap-2"
                    >
                        {emotes.map((emoji) => (
                            <button
                                key={emoji}
                                onClick={() => { onSelect(emoji); onClose(); }}
                                className="w-12 h-12 flex items-center justify-center text-2xl hover:bg-white/10 rounded-xl transition-colors active:scale-95"
                            >
                                {emoji}
                            </button>
                        ))}
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};
