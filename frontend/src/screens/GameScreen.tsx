import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore } from '../store';
import { GamePhase } from '../types';
import { BettingStatusBar } from '../components/GameComponents';
import { ChatBoard } from '../components/ChatBoard';
import { Button } from '../components/UIComponents';
import { NightOverlay } from '../components/NightOverlay';
import { NightActionPanel } from '../components/NightActionPanel';
import { RoleRevealModal } from '../components/RoleRevealModal';
import { useChatBubbles } from '../hooks/useChatBubbles';
import { useCountdown } from '../hooks/useCountdown';
import { useNightOverlay } from '../hooks/useNightOverlay';
import { useActionTimeout } from '../hooks/useActionTimeout';
import { GameBackground } from '../components/shared/GameBackground';
import { GameHeader } from '../components/shared/GameHeader';
import { PhaseIndicator } from '../components/shared/PhaseIndicator';
import { PlayerGrid } from '../components/shared/PlayerGrid';
import { TIMING } from '../constants/timing';
import { MessageSquare, EyeOff, AlertCircle } from 'lucide-react';

export const GameScreen = () => {
  const { players, phase, round, triggerReveal, messages, activeEmotes, currentAction, submitActionResponse } = useGameStore();
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [showRoleReveal, setShowRoleReveal] = useState(true);

  const activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Custom hooks
  const chatBubbles = useChatBubbles(messages);
  const showNightOverlay = useNightOverlay(phase);
  const [timeLeft, setTimeLeft] = useCountdown(0);
  useActionTimeout(currentAction, setTimeLeft);

  // Track active speaker separately from chat bubbles
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

  // Cleanup speaker timer on unmount
  useEffect(() => {
    return () => {
      if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
    };
  }, []);

  // Handle vote via action response
  const handleVote = (playerId: string) => {
    if (!currentAction || currentAction.actionType !== 'vote') return;
    const player = players.find(p => p.id === playerId);
    if (player && currentAction.options.includes(player.name)) {
      submitActionResponse(player.name);
    }
  };

  const humanPlayer = players.find(p => !p.isAi);
  const showVoteButtons = currentAction?.actionType === 'vote';
  const showNightActionUI = currentAction?.actionType === 'night_action' && phase === GamePhase.NIGHT;

  return (
    <GameBackground phase={phase}>

      <NightOverlay show={showNightOverlay} />

      <NightActionPanel
        show={showNightActionUI}
        currentAction={currentAction}
        timeLeft={timeLeft}
        onAction={(targetName) => submitActionResponse(targetName)}
      />

      <RoleRevealModal
        show={showRoleReveal}
        role={humanPlayer?.role}
        onDismiss={() => setShowRoleReveal(false)}
      />

      {/* Header */}
      <GameHeader
        left={
          <span
            className="text-xl font-black tracking-tight text-transparent bg-clip-text"
            style={{
              backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
              filter: 'drop-shadow(0 0 10px rgba(212,168,83,0.3))',
            }}
          >MAFI-AI</span>
        }
        center={<PhaseIndicator phase={phase} round={round} timeLeft={timeLeft} />}
        right={
          <div className="flex items-center gap-6">
            {currentAction && (
              <div className="hidden md:flex items-center gap-2 text-gold animate-pulse">
                <AlertCircle className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-wider">
                  {currentAction.actionType === 'vote' ? 'Vote Now' :
                   currentAction.actionType === 'statement' ? 'Your Turn' :
                   'Choose Target'}
                </span>
              </div>
            )}
            <Button variant="ghost" size="sm" onClick={triggerReveal} className="text-white/20 hover:text-white px-2">
              <EyeOff className="w-4 h-4" />
            </Button>
          </div>
        }
      />

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative z-[2]">

        {/* Center: The Board (Player Grid) */}
        <div className="flex-1 h-full relative p-4 lg:p-10 flex flex-col items-center justify-center z-40 pointer-events-none overflow-visible">

          {/* Floating Betting Status Bar */}
          <BettingStatusBar />

          {/* Players Grid Layout */}
          <PlayerGrid
            players={players}
            activeSpeakerId={activeSpeakerId}
            chatBubbles={chatBubbles}
            activeEmotes={activeEmotes}
            onVote={handleVote}
            showVoteButton={showVoteButtons}
          />

          {/* Mobile chat toggle */}
          <div className="absolute bottom-6 left-6 z-40 pointer-events-auto md:hidden">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsChatOpen(!isChatOpen)}
              className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(0,0,0,0.5)] border transition-all duration-300 ${
                isChatOpen
                  ? 'bg-gold border-white text-black'
                  : 'bg-[#1e293b] border-white/20 text-white hover:border-gold/50 hover:text-gold'
              }`}
            >
              <MessageSquare className="w-6 h-6" />
            </motion.button>
          </div>
        </div>

        {/* Right: Fixed Chat Panel */}
        <div className="hidden md:flex w-[340px] shrink-0 h-full border-l border-white/5 z-50">
          <ChatBoard />
        </div>

        {/* Mobile Chat Drawer */}
        <AnimatePresence>
          {isChatOpen && (
            <motion.div
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="md:hidden absolute top-0 right-0 bottom-0 w-full z-50"
            >
              <ChatBoard onClose={() => setIsChatOpen(false)} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </GameBackground>
  );
};
