import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useGameStore } from '../store';
import { BettingStatusBar } from '../components/GameComponents';
import { useChatBubbles } from '../hooks/useChatBubbles';
import { useCountdown } from '../hooks/useCountdown';
import { GameBackground } from '../components/shared/GameBackground';
import { GameHeader } from '../components/shared/GameHeader';
import { PhaseIndicator } from '../components/shared/PhaseIndicator';
import { PlayerGrid } from '../components/shared/PlayerGrid';
import { BettingPanel } from '../components/BettingPanel';
import { SpecChatPanel } from '../components/SpecChatPanel';
import { TIMING } from '../constants/timing';
import {
  Eye, DollarSign, LogOut, MessageSquare, X,
} from 'lucide-react';

export const SpectatorScreen = () => {
  const {
    players, phase, round, messages,
    activeEmotes, usdcBets, usdcBalance,
    placeBetUSDC, resetGame, odds,
  } = useGameStore();

  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [timeLeft] = useCountdown(0);
  const chatBubbles = useChatBubbles(messages);
  const activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [isSpecChatOpen, setIsSpecChatOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Track active speaker from messages
  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1]!;
      if (lastMsg.type === 'chat') {
        const senderId = lastMsg.senderId;
        setActiveSpeakerId(senderId);
        if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
        activeSpeakerTimerRef.current = setTimeout(() => setActiveSpeakerId(null), TIMING.ACTIVE_SPEAKER_TIMEOUT);
      }
    }
  }, [messages]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
    };
  }, []);

  const handleOpenChat = () => {
    setIsSpecChatOpen(true);
    setUnreadCount(0);
  };

  return (
    <GameBackground phase={phase}>

      {/* Header */}
      <GameHeader
        left={
          <>
            <span
              className="text-xl font-black tracking-tight text-transparent bg-clip-text"
              style={{
                backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
                filter: 'drop-shadow(0 0 10px rgba(212,168,83,0.3))',
              }}
            >MAFI-AI</span>
            <div className="px-2 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 text-[9px] font-bold uppercase tracking-widest flex items-center gap-1">
              <Eye className="w-3 h-3" /> Spectator
            </div>
          </>
        }
        center={<PhaseIndicator phase={phase} round={round} timeLeft={timeLeft} />}
        right={
          <>
            <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-full">
              <DollarSign className="w-3.5 h-3.5 text-green-400" />
              <span className="text-sm font-mono font-bold text-green-400">{usdcBalance.toFixed(2)}</span>
              <span className="text-[9px] text-green-400/60 font-bold">USDC</span>
            </div>
            <button onClick={resetGame} className="p-2 hover:bg-white/5 rounded-full text-white/30 hover:text-white transition-colors">
              <LogOut className="w-4 h-4" />
            </button>
          </>
        }
      />

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative z-[2]">

        {/* Left: Game View */}
        <div className="flex-1 h-full relative p-4 lg:p-8 flex flex-col items-center justify-center z-40 pointer-events-none overflow-visible">
          <BettingStatusBar />

          <PlayerGrid
            players={players}
            activeSpeakerId={activeSpeakerId}
            chatBubbles={chatBubbles}
            activeEmotes={activeEmotes}
          />
        </div>

        {/* Spectator Chat Toggle Button */}
        <div className="absolute bottom-6 left-6 z-[60] pointer-events-auto">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => (isSpecChatOpen ? setIsSpecChatOpen(false) : handleOpenChat())}
            className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(0,0,0,0.5)] border transition-all duration-300 relative ${
              isSpecChatOpen
                ? 'bg-purple-500 border-purple-300 text-white'
                : 'bg-[#1e293b] border-white/20 text-white hover:border-purple-400/50 hover:text-purple-300'
            }`}
          >
            {isSpecChatOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
            {unreadCount > 0 && !isSpecChatOpen && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-bold flex items-center justify-center border-2 border-[#1e293b]"
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </motion.div>
            )}
          </motion.button>
        </div>

        {/* Spectator Chat Panel */}
        <SpecChatPanel
          isOpen={isSpecChatOpen}
          onClose={() => setIsSpecChatOpen(false)}
          onUnreadChange={() => setUnreadCount(prev => prev + 1)}
        />

        {/* Right: Betting Panel */}
        <BettingPanel
          players={players}
          odds={odds}
          usdcBalance={usdcBalance}
          usdcBets={usdcBets}
          messages={messages}
          placeBetUSDC={placeBetUSDC}
        />
      </main>
    </GameBackground>
  );
};
