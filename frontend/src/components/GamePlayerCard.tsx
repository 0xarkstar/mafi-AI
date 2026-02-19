import { Player, Role } from '../types';
import { AVATAR_IMAGES } from '../constants';
import { GlassCard } from './UIComponents';
import { motion, AnimatePresence } from 'framer-motion';
import { Target, Skull, Shield, Sword, Eye } from 'lucide-react';

interface GamePlayerCardProps {
  player: Player;
  isSpeaking?: boolean;
  onVote?: (id: string) => void;
  showVoteButton?: boolean;
  votesReceived?: number;
  currentMessage?: string | null;
  activeEmote?: string;
}

export const GamePlayerCard = ({ player, isSpeaking, onVote, showVoteButton, votesReceived = 0, currentMessage, activeEmote }: GamePlayerCardProps) => {
  const canVote = showVoteButton && !player.isDead;

  return (
    <div
        className={`relative w-full aspect-[4/5] max-w-[200px] mx-auto group ${currentMessage || activeEmote ? 'z-50' : 'z-0'} pointer-events-auto ${canVote ? 'cursor-pointer' : ''}`}
        onClick={() => canVote && onVote?.(player.id)}
    >

        {/* Chat Bubble Overlay */}
        <AnimatePresence>
            {currentMessage && (
                <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.9 }}
                    animate={{ opacity: 1, y: -20, scale: 1 }}
                    exit={{ opacity: 0, y: 0, scale: 0.9 }}
                    className="absolute bottom-full left-0 right-0 mb-2 z-[60] pointer-events-none flex justify-center"
                >
                    <div className="bg-[#1e293b] text-white text-xs font-medium p-3 rounded-2xl shadow-[0_4px_20px_rgba(0,0,0,0.5)] border border-gold/40 relative text-center max-w-[220px] w-max">
                        <span className="text-gold font-bold uppercase text-[9px] block mb-1 opacity-70">{player.name}</span>
                        <p className="leading-snug">{currentMessage}</p>
                        {/* Arrow pointing down */}
                        <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-[#1e293b] border-b border-r border-gold/40 transform rotate-45" />
                    </div>
                </motion.div>
            )}
        </AnimatePresence>

        {/* Emote Overlay */}
        <AnimatePresence>
            {activeEmote && (
                <motion.div
                    initial={{ opacity: 0, y: 0, scale: 0.5 }}
                    animate={{ opacity: 1, y: -60, scale: 1.2 }}
                    exit={{ opacity: 0, y: -80, scale: 0.8 }}
                    transition={{ type: "spring", stiffness: 200, damping: 15 }}
                    className="absolute top-0 right-0 z-[70] pointer-events-none"
                >
                    <div className="text-4xl filter drop-shadow-[0_0_15px_rgba(255,255,255,0.4)]">
                        {activeEmote}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>

        <GlassCard className={`w-full h-full flex flex-col items-center justify-end p-0 transition-all duration-300 relative overflow-hidden
            ${player.isDead ? 'border-red-900/30' :
              isSpeaking ? 'border-gold shadow-[0_0_25px_rgba(212,168,83,0.3)] scale-105 z-10' :
              canVote ? 'border-white/10 hover:border-red-500/60 hover:shadow-[0_0_20px_rgba(239,68,68,0.3)]' :
              'border-white/10 hover:border-white/30'}`}>

            {/* Full card avatar image */}
            {player.avatarIndex != null ? (
              <img src={AVATAR_IMAGES[player.avatarIndex]} alt={player.name} className={`absolute inset-0 w-full h-full object-cover ${player.isDead ? 'grayscale opacity-40' : ''}`} />
            ) : (
              <div className={`absolute inset-0 flex items-center justify-center ${player.isDead ? 'bg-black/80' : 'bg-gradient-to-b from-[#0f172a]/80 to-black/60'}`}>
                <div className={`w-16 h-16 ${player.isDead ? 'text-gray-700' : isSpeaking ? 'text-gold' : 'text-blue-400'}`} />
              </div>
            )}

            {/* Bottom gradient overlay */}
            <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/90 via-black/50 to-transparent z-10" />

            {/* Speaking border glow */}
            {isSpeaking && !player.isDead && (
                <div className="absolute inset-0 border-2 border-gold rounded-xl z-20 shadow-[inset_0_0_20px_rgba(212,168,83,0.2)]" />
            )}

            {/* Vote hover overlay */}
            {canVote && (
                <div className="absolute inset-0 z-20 bg-red-600/0 group-hover:bg-red-600/20 transition-colors duration-300 flex items-center justify-center">
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center gap-1"
                    >
                        <Target className="w-8 h-8 text-red-400 drop-shadow-[0_0_10px_rgba(239,68,68,0.6)]" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-red-400 drop-shadow-lg">Vote</span>
                    </motion.div>
                </div>
            )}

            {/* Top Status: Votes */}
            <div className="absolute top-2 right-2 z-30">
                {votesReceived > 0 && (
                    <motion.div
                        initial={{ scale: 0 }} animate={{ scale: 1 }}
                        className="bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-lg border border-red-400 flex items-center gap-1"
                    >
                        <Target className="w-3 h-3" /> {votesReceived}
                    </motion.div>
                )}
            </div>

            {/* Dead Overlay */}
            {player.isDead && (
                <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/50 backdrop-blur-[2px]">
                    <Skull className="w-14 h-14 text-red-600 drop-shadow-[0_0_10px_rgba(220,38,38,0.8)]" />
                </div>
            )}

            {/* Role Badge — only visible for the human player */}
            {player.role && !player.isAi && (
                <div className="absolute top-2 left-2 z-30">
                     <div className={`w-7 h-7 rounded-full border-2 flex items-center justify-center shadow-lg bg-black/60 backdrop-blur-sm ${
                         player.role === Role.MAFIA ? 'border-red-500 text-red-500' :
                         player.role === Role.DETECTIVE ? 'border-blue-500 text-blue-500' :
                         'border-green-500 text-green-500'
                     }`}>
                         {player.role === Role.MAFIA ? <Sword className="w-3.5 h-3.5" /> :
                          player.role === Role.DETECTIVE ? <Eye className="w-3.5 h-3.5" /> :
                          <Shield className="w-3.5 h-3.5" />}
                     </div>
                </div>
            )}

            {/* Info Section */}
            <div className="relative z-20 text-center w-full p-3">
                <div className={`font-bold text-sm tracking-wide truncate px-1 drop-shadow-lg ${player.isDead ? 'text-white/30 line-through decoration-red-900' : 'text-white'}`}>
                    {player.name}
                </div>
                <div className="text-[9px] text-white/40 uppercase tracking-widest font-bold mt-0.5 drop-shadow">
                    {player.isDead ? 'ELIMINATED' : player.trait}
                </div>
            </div>
        </GlassCard>
    </div>
  );
};
