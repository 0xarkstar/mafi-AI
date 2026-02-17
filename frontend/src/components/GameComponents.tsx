import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import { Player, Role, AVATAR_IMAGES } from '../types';
import { GlassCard, Input } from './UIComponents';
import { motion, AnimatePresence } from 'framer-motion';
import { User, MessageSquare, Target, Send, Skull, Shield, Sword, Zap, Flame, Star, Moon, Hexagon, Diamond, Eye, X, TrendingUp, Smile } from 'lucide-react';
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

// --- Game Player Card (Main Board Grid) ---
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
                <AvatarIcon name={player.avatarIcon} className={`w-16 h-16 ${player.isDead ? 'text-gray-700' : isSpeaking ? 'text-gold' : 'text-blue-400'}`} />
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

// --- Chat Board (Drawer/Panel Mode) ---
interface ChatBoardProps {
    onClose?: () => void;
}

export const ChatBoard = ({ onClose }: ChatBoardProps) => {
  const { messages, addMessage, nickname, triggerEmote, currentAction, submitActionResponse } = useGameStore();
  const [input, setInput] = useState('');
  const [isEmoteOpen, setIsEmoteOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isStatementTurn = currentAction?.actionType === 'statement';

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (isStatementTurn) {
      // Send as action response to backend
      submitActionResponse(input.trim());
    } else {
      // Local message (visible only to self)
      addMessage({
        senderId: 'human-1',
        senderName: nickname,
        text: input,
        type: 'chat',
        color: '#ffffff'
      });
    }
    setInput('');
  };

  return (
    <div className="h-full flex flex-col relative bg-[#030712]/95 backdrop-blur-xl border-r border-white/5 shadow-2xl">
      {/* Top Bar */}
      <div className="h-14 bg-black/40 border-b border-white/5 flex items-center justify-between px-4">
         <div className="flex items-center gap-2 text-gold text-xs uppercase tracking-[0.15em] font-bold">
            <MessageSquare className="w-4 h-4" />
            <span>{isStatementTurn ? 'Your Turn to Speak' : 'Encrypted Channel'}</span>
         </div>
         {onClose && (
             <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-white/50 hover:text-white transition-colors">
                 <X className="w-5 h-5" />
             </button>
         )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-white/20 gap-4">
             <MessageSquare className="w-10 h-10 opacity-20" />
             <p className="text-xs uppercase tracking-widest">No signals detected...</p>
          </div>
        )}

        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className={`flex flex-col ${msg.senderId === 'human-1' ? 'items-end' : 'items-start'}`}
          >
            {msg.type === 'system' ? (
               <div className="w-full text-center my-3">
                 <span className="text-[9px] uppercase tracking-[0.15em] text-white/30 bg-white/5 px-2 py-1 rounded-full">{msg.text}</span>
               </div>
            ) : msg.type === 'elimination' ? (
                <div className="w-full flex items-center justify-center my-2">
                    <div className="bg-red-950/40 border border-red-500/30 px-4 py-1.5 rounded text-red-400 text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                        <Skull className="w-3 h-3" /> {msg.text}
                    </div>
                </div>
            ) : (
              <div className={`max-w-[85%] flex flex-col gap-1 ${msg.senderId === 'human-1' ? 'items-end' : 'items-start'}`}>
                <div className="flex items-center gap-2 px-1">
                    <span className="text-[10px] font-bold" style={{ color: msg.color || '#fff' }}>{msg.senderName}</span>
                    <span className="text-[9px] text-white/20">{new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div className={`px-3 py-2 rounded-lg text-sm leading-relaxed shadow-sm border ${
                    msg.senderId === 'human-1'
                    ? 'bg-[#d4a853]/10 text-white border-[#d4a853]/30 rounded-tr-none'
                    : 'bg-[#1e293b] text-white/90 border-white/10 rounded-tl-none'
                }`}>
                    {msg.text}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-3 bg-black/60 border-t border-white/5">
        <form onSubmit={handleSend} className="relative flex items-center gap-2">
            <div className="relative">
                <button
                    type="button"
                    onClick={() => setIsEmoteOpen(!isEmoteOpen)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center border transition-all duration-300 shrink-0 ${
                        isEmoteOpen
                        ? 'bg-white/20 border-white text-white'
                        : 'bg-white/5 border-white/10 text-white/50 hover:border-gold/50 hover:text-gold'
                    }`}
                >
                    <Smile className="w-5 h-5" />
                </button>
                <EmoteMenu
                    isOpen={isEmoteOpen}
                    onClose={() => setIsEmoteOpen(false)}
                    onSelect={(emote) => { triggerEmote('human-1', emote); setIsEmoteOpen(false); }}
                />
            </div>
            <div className="relative flex-1">
                <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isStatementTurn ? "Share your thoughts..." : "Type message..."}
                    className="pl-3 pr-10 py-3 bg-white/5 border-white/10 focus:border-gold/50 rounded-lg text-sm w-full"
                />
                <button
                    type="submit"
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 p-2 text-gold hover:text-white transition-colors disabled:opacity-30"
                    disabled={!input}
                >
                    <Send className="w-4 h-4" />
                </button>
            </div>
        </form>
      </div>
    </div>
  );
};

// --- Betting Panel (Placeholder) ---
export const BettingPanel = () => {
    return null;
};
