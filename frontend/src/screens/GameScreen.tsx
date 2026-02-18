import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore } from '../store';
import { GamePhase, Role } from '../types';
import { GamePlayerCard, ChatBoard, BettingStatusBar } from '../components/GameComponents';
import { Button } from '../components/UIComponents';
import { Sun, Moon, EyeOff, MessageSquare, Shield, Sword, Eye as EyeIcon, Target, AlertCircle } from 'lucide-react';

export const GameScreen = () => {
  const { players, phase, round, triggerReveal, messages, activeEmotes, currentAction, submitActionResponse } = useGameStore();
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [showNightOverlay, setShowNightOverlay] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const [timeLeft, setTimeLeft] = useState(0);
  const [showRoleReveal, setShowRoleReveal] = useState(true);

  // Real-time bubble state mapping
  const [chatBubbles, setChatBubbles] = useState<Record<string, string>>({});
  const bubbleTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Chat bubble tracking from messages
  useEffect(() => {
    if (messages.length > 0) {
        const lastMsg = messages[messages.length - 1]!;
        if (lastMsg.type === 'chat') {
            const senderId = lastMsg.senderId;

            // Set the speaking indicator
            setActiveSpeakerId(senderId);
            if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
            activeSpeakerTimerRef.current = setTimeout(() => setActiveSpeakerId(null), 3000);

            setChatBubbles(prev => ({
                ...prev,
                [senderId]: lastMsg.text
            }));

            if (bubbleTimers.current[senderId]) {
                clearTimeout(bubbleTimers.current[senderId]);
            }

            bubbleTimers.current[senderId] = setTimeout(() => {
                setChatBubbles(prev => {
                    const newState = { ...prev };
                    delete newState[senderId];
                    return newState;
                });
                delete bubbleTimers.current[senderId];
            }, 5000);
        }
    }
  }, [messages]);

  // Show night overlay on phase change to night
  useEffect(() => {
    if (phase === GamePhase.NIGHT) {
      setShowNightOverlay(true);
      const timer = setTimeout(() => setShowNightOverlay(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [phase]);

  // Set countdown from action request timeout
  useEffect(() => {
    if (currentAction) {
      setTimeLeft(currentAction.timeout);
    }
  }, [currentAction]);

  // Countdown Logic
  useEffect(() => {
    if (timeLeft > 0) {
        const timerId = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
        return () => clearTimeout(timerId);
    }
  }, [timeLeft]);

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

  // Handle night action target selection
  const handleNightAction = (targetName: string) => {
    if (!currentAction || currentAction.actionType !== 'night_action') return;
    submitActionResponse(targetName);
  };

  const showVoteButtons = currentAction?.actionType === 'vote';
  const showNightActionUI = currentAction?.actionType === 'night_action' && phase === GamePhase.NIGHT;

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden relative bg-[#050505]">
      {/* Background Images — crossfade between day and night */}
      <img src="/images/game-bg.png" alt="" className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-0' : 'opacity-100'}`} />
      <img src="/images/game-bg-night.png" alt="" className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-100' : 'opacity-0'}`} />
      {/* Phase-tinted overlay */}
      <div className={`absolute inset-0 transition-all duration-[2000ms] z-[1] pointer-events-none
        ${phase === GamePhase.NIGHT ? 'bg-[#0a0e1f]/60' :
          phase === GamePhase.DAY_VOTE ? 'bg-[#1a0505]/70' :
          'bg-[#0a0a05]/50'}`}
      />

      {/* Night Overlay */}
      <AnimatePresence>
        {showNightOverlay && (
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
                        transition={{ duration: 3, ease: "circOut" }}
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

      {/* Night Action Overlay (for Mafia/Detective) */}
      <AnimatePresence>
        {showNightActionUI && currentAction && (
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
                    onClick={() => handleNightAction(name)}
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

      {/* Role Reveal Modal */}
      <AnimatePresence>
        {showRoleReveal && (() => {
            const humanPlayer = players.find(p => !p.isAi);
            const role = humanPlayer?.role;
            const roleConfig = role === Role.MAFIA
                ? { label: 'MAFIA', desc: 'Eliminate citizens without being caught. Vote strategically during the day.', color: 'text-red-500', border: 'border-red-500', bg: 'bg-red-500/10', glow: 'rgba(239,68,68,0.4)', icon: <Sword className="w-16 h-16" /> }
                : role === Role.DETECTIVE
                ? { label: 'DETECTIVE', desc: 'Investigate one player each night to learn their true identity.', color: 'text-blue-400', border: 'border-blue-400', bg: 'bg-blue-500/10', glow: 'rgba(96,165,250,0.4)', icon: <EyeIcon className="w-16 h-16" /> }
                : { label: 'CITIZEN', desc: 'Find and vote out the Mafia before they eliminate everyone.', color: 'text-green-400', border: 'border-green-400', bg: 'bg-green-500/10', glow: 'rgba(74,222,128,0.4)', icon: <Shield className="w-16 h-16" /> };
            return (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-sm"
                >
                    <motion.div
                        initial={{ scale: 0.7, opacity: 0, y: 30 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
                        className="flex flex-col items-center gap-6 text-center max-w-sm px-6"
                    >
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.3, type: 'spring', stiffness: 300 }}
                            className="text-xs font-bold uppercase tracking-[0.3em] text-white/40"
                        >
                            Your Role
                        </motion.div>

                        <motion.div
                            initial={{ scale: 0, rotate: -180 }}
                            animate={{ scale: 1, rotate: 0 }}
                            transition={{ delay: 0.5, type: 'spring', stiffness: 200, damping: 15 }}
                            className={`w-28 h-28 rounded-full ${roleConfig.border} border-2 ${roleConfig.bg} flex items-center justify-center ${roleConfig.color}`}
                            style={{ boxShadow: `0 0 60px ${roleConfig.glow}` }}
                        >
                            {roleConfig.icon}
                        </motion.div>

                        <motion.h2
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 0.8 }}
                            className={`text-5xl font-black tracking-[0.2em] ${roleConfig.color}`}
                            style={{ textShadow: `0 0 30px ${roleConfig.glow}` }}
                        >
                            {roleConfig.label}
                        </motion.h2>

                        <motion.p
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 1.0 }}
                            className="text-white/50 text-sm leading-relaxed max-w-[280px]"
                        >
                            {roleConfig.desc}
                        </motion.p>

                        <motion.button
                            initial={{ y: 20, opacity: 0 }}
                            animate={{ y: 0, opacity: 1 }}
                            transition={{ delay: 1.3 }}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => setShowRoleReveal(false)}
                            className={`mt-4 px-10 py-3 rounded-full ${roleConfig.border} border ${roleConfig.bg} ${roleConfig.color} font-bold text-sm uppercase tracking-widest hover:bg-white/10 transition-colors`}
                        >
                            Start Game
                        </motion.button>
                    </motion.div>
                </motion.div>
            );
        })()}
      </AnimatePresence>

      {/* Header */}
      <header className="h-16 px-6 flex items-center justify-between bg-[#030712]/80 backdrop-blur-md border-b border-white/5 z-[10] shrink-0 relative">
         {/* Left: Logo */}
         <div className="flex items-center gap-3">
             <span
               className="text-xl font-black tracking-tight text-transparent bg-clip-text"
               style={{
                 backgroundImage: 'linear-gradient(180deg, #FFF2CC 0%, #D4A853 50%, #805F1F 100%)',
                 filter: 'drop-shadow(0 0 10px rgba(212,168,83,0.3))',
               }}
             >MAFI-AI</span>
         </div>

         {/* Center: Phase Indicator & Timer */}
         <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-3 bg-white/5 px-4 py-1.5 rounded-full border border-white/5 shadow-inner">
             {phase === GamePhase.NIGHT ? <Moon className="w-4 h-4 text-indigo-400" /> : <Sun className="w-4 h-4 text-orange-400" />}
             <span className="text-xs font-bold uppercase w-20 text-center text-white/80">{phase.replace('_', ' ')}</span>
             <div className="w-px h-3 bg-white/10" />
             <div className="text-xs font-mono text-white/40">ROUND {round}</div>
             <div className="w-px h-3 bg-white/10" />
             <div className={`text-xs font-mono font-bold w-12 text-center ${timeLeft <= 5 ? 'text-red-500 animate-pulse' : 'text-white/60'}`}>
                00:{timeLeft.toString().padStart(2, '0')}
             </div>
         </div>

         {/* Right: Action Status & Reveal */}
         <div className="flex items-center gap-6">
            {/* Action prompt indicator */}
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
      </header>

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative z-[2]">

         {/* Center: The Board (Player Grid) */}
         <div className="flex-1 h-full relative p-4 lg:p-10 flex flex-col items-center justify-center z-40 pointer-events-none overflow-visible">

            {/* Floating Betting Status Bar */}
            <BettingStatusBar />

            {/* Players Grid Layout */}
            <div className="w-full max-w-5xl flex flex-col gap-8 md:gap-12 relative z-10 overflow-visible">

                {/* Top Row (4 Agents) */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 justify-items-center overflow-visible">
                    {players.slice(0, 4).map(p => (
                        <GamePlayerCard
                            key={p.id}
                            player={p}
                            isSpeaking={activeSpeakerId === p.id}
                            onVote={handleVote}
                            showVoteButton={showVoteButtons}
                            currentMessage={chatBubbles[p.id]}
                            activeEmote={activeEmotes[p.id]}
                        />
                    ))}
                </div>

                {/* Bottom Row (3 Players) */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 justify-items-center w-full md:w-4/5 mx-auto overflow-visible">
                     {players.slice(4, 7).map(p => (
                        <GamePlayerCard
                            key={p.id}
                            player={p}
                            isSpeaking={activeSpeakerId === p.id}
                            onVote={handleVote}
                            showVoteButton={showVoteButtons}
                            currentMessage={chatBubbles[p.id]}
                            activeEmote={activeEmotes[p.id]}
                        />
                    ))}
                </div>
            </div>

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
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="md:hidden absolute top-0 right-0 bottom-0 w-full z-50"
                 >
                     <ChatBoard onClose={() => setIsChatOpen(false)} />
                 </motion.div>
             )}
         </AnimatePresence>
      </main>
    </div>
  );
};
