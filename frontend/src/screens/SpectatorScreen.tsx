import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useGameStore } from '../store';
import { GamePhase, AVATAR_IMAGES, BetType } from '../types';
import { GamePlayerCard, BettingStatusBar } from '../components/GameComponents';
import { GlassCard, Button, Input } from '../components/UIComponents';
import {
  Sun, Moon, TrendingUp, Eye, Users, Target, ChevronDown,
  DollarSign, ArrowRight, Clock, Zap, BarChart3,
  MessageSquare, Skull, LogOut, Send, X,
} from 'lucide-react';

const BET_TYPES: { value: BetType; label: string; desc: string; icon: React.ReactNode }[] = [
  { value: 'side_win', label: 'Side Win', desc: 'Who wins the game?', icon: <Users className="w-4 h-4" /> },
  { value: 'next_elimination', label: 'Next Out', desc: 'Who gets eliminated next?', icon: <Target className="w-4 h-4" /> },
  { value: 'is_mafia', label: 'Is Mafia?', desc: 'Is this player Mafia?', icon: <Eye className="w-4 h-4" /> },
  { value: 'is_ai_or_human', label: 'AI or Human?', desc: 'Is this player AI or Human?', icon: <Zap className="w-4 h-4" /> },
];

export const SpectatorScreen = () => {
  const {
    players, phase, round, messages,
    activeEmotes, usdcBets, usdcBalance,
    placeBetUSDC, resetGame, odds,
  } = useGameStore();

  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);
  const [chatBubbles, setChatBubbles] = useState<Record<string, string>>({});
  const bubbleTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const betSuccessTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Betting panel state
  const [selectedBetType, setSelectedBetType] = useState<BetType>('side_win');
  const [betTarget, setBetTarget] = useState('');
  const [betAmount, setBetAmount] = useState('');
  const [showBetTypeDropdown, setShowBetTypeDropdown] = useState(false);
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);
  const [betSuccess, setBetSuccess] = useState(false);

  // Spectator chat
  const [isSpecChatOpen, setIsSpecChatOpen] = useState(false);
  const [specChatInput, setSpecChatInput] = useState('');
  const [specMessages, setSpecMessages] = useState<{ id: string; name: string; text: string; time: number; isMe: boolean }[]>([]);
  const specChatScrollRef = useRef<HTMLDivElement>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  // Simulated spectator chat from other viewers
  useEffect(() => {
    const specNames = ['Whale_0x', 'CryptoNerd', 'MonadFan', 'BetKing', 'DeFiDegen', 'MafiaWatcher', 'LurkMaster'];
    const specLines = [
      'Viktor is definitely sus',
      'lol Nova is playing it cool',
      'anyone else think Iris is mafia?',
      'just went all in on Citizens',
      'this round is crazy',
      'mafia is so obvious rn',
      'no way they vote out Luna',
      'GG ez citizens win',
      'that elimination was huge',
      'I think it\'s Rex tbh',
      'who else is betting?',
      'odds just shifted hard',
      'night phase incoming...',
      'calling it now, Blaze is mafia',
      'Sage is playing 4D chess',
    ];
    const interval = setInterval(() => {
      if (Math.random() > 0.55) {
        const name = specNames[Math.floor(Math.random() * specNames.length)]!;
        const text = specLines[Math.floor(Math.random() * specLines.length)]!;
        const msg = { id: Math.random().toString(36).substr(2, 9), name, text, time: Date.now(), isMe: false };
        setSpecMessages(prev => [...prev, msg].slice(-50));
        if (!isSpecChatOpen) setUnreadCount(prev => prev + 1);
      }
    }, 4000 + Math.random() * 3000);
    return () => clearInterval(interval);
  }, [isSpecChatOpen]);

  // Auto-scroll spectator chat
  useEffect(() => {
    if (specChatScrollRef.current) {
      specChatScrollRef.current.scrollTop = specChatScrollRef.current.scrollHeight;
    }
  }, [specMessages]);

  const handleSpecChatSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!specChatInput.trim()) return;
    const msg = {
      id: Math.random().toString(36).substr(2, 9),
      name: 'You',
      text: specChatInput.trim(),
      time: Date.now(),
      isMe: true,
    };
    setSpecMessages(prev => [...prev, msg].slice(-50));
    setSpecChatInput('');
  };

  // Chat bubbles from real WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1]!;
      if (lastMsg.type === 'chat') {
        const senderId = lastMsg.senderId;

        setActiveSpeakerId(senderId);
        if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
        activeSpeakerTimerRef.current = setTimeout(() => setActiveSpeakerId(null), 3000);

        setChatBubbles(prev => ({ ...prev, [senderId]: lastMsg.text }));
        if (bubbleTimers.current[senderId]) clearTimeout(bubbleTimers.current[senderId]);
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

  // Countdown
  useEffect(() => {
    if (timeLeft > 0) {
      const timerId = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timerId);
    }
  }, [timeLeft]);

  // Derive live odds from store
  const mafiaOdds = odds ? (1 / odds.mafiaWinProb).toFixed(2) : '—';
  const citizenOdds = odds ? (1 / odds.citizenWinProb).toFixed(2) : '—';

  const getTargetOptions = () => {
    if (selectedBetType === 'side_win') return ['Mafia', 'Citizens'];
    if (selectedBetType === 'is_ai_or_human') {
      return players.filter(p => !p.isDead).map(p => p.name);
    }
    return players.filter(p => !p.isDead).map(p => p.name);
  };

  const handlePlaceBet = () => {
    const amt = parseFloat(betAmount);
    if (!betTarget || isNaN(amt) || amt < 1.0 || amt > usdcBalance) return;
    placeBetUSDC(selectedBetType, betTarget, amt);
    setBetSuccess(true);
    setBetAmount('');
    setBetTarget('');
    if (betSuccessTimerRef.current) clearTimeout(betSuccessTimerRef.current);
    betSuccessTimerRef.current = setTimeout(() => setBetSuccess(false), 2000);
  };

  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  // Cleanup all timeouts on unmount
  useEffect(() => {
    return () => {
      if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
      if (betSuccessTimerRef.current) clearTimeout(betSuccessTimerRef.current);
    };
  }, []);

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden relative bg-[#050505]">
      {/* Background Images */}
      <img src="/images/game-bg.png" alt="" className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-0' : 'opacity-100'}`} />
      <img src="/images/game-bg-night.png" alt="" className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-100' : 'opacity-0'}`} />
      <div className={`absolute inset-0 transition-all duration-[2000ms] z-[1] pointer-events-none
        ${phase === GamePhase.NIGHT ? 'bg-[#0a0e1f]/60' :
          phase === GamePhase.DAY_VOTE ? 'bg-[#1a0505]/70' :
          'bg-[#0a0a05]/50'}`}
      />

      {/* Header */}
      <header className="h-16 px-6 flex items-center justify-between bg-[#030712]/80 backdrop-blur-md border-b border-white/5 z-[10] shrink-0 relative">
        <div className="flex items-center gap-3">
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
        </div>

        {/* Center: Phase Indicator */}
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

        {/* Right: Balance + Exit */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-full">
            <DollarSign className="w-3.5 h-3.5 text-green-400" />
            <span className="text-sm font-mono font-bold text-green-400">{usdcBalance.toFixed(2)}</span>
            <span className="text-[9px] text-green-400/60 font-bold">USDC</span>
          </div>
          <button onClick={resetGame} className="p-2 hover:bg-white/5 rounded-full text-white/30 hover:text-white transition-colors">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <main className="flex-1 flex overflow-hidden relative z-[2]">

        {/* Left: Game View */}
        <div className="flex-1 h-full relative p-4 lg:p-8 flex flex-col items-center justify-center z-40 pointer-events-none overflow-visible">
          <BettingStatusBar />

          <div className="w-full max-w-5xl flex flex-col gap-8 md:gap-12 relative z-10 overflow-visible">
            {/* Top Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 justify-items-center overflow-visible">
              {players.slice(0, 4).map(p => (
                <GamePlayerCard
                  key={p.id}
                  player={p}
                  isSpeaking={activeSpeakerId === p.id}
                  currentMessage={chatBubbles[p.id]}
                  activeEmote={activeEmotes[p.id]}
                />
              ))}
            </div>
            {/* Bottom Row */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-8 justify-items-center w-full md:w-4/5 mx-auto overflow-visible">
              {players.slice(4, 7).map(p => (
                <GamePlayerCard
                  key={p.id}
                  player={p}
                  isSpeaking={activeSpeakerId === p.id}
                  currentMessage={chatBubbles[p.id]}
                  activeEmote={activeEmotes[p.id]}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Spectator Chat Toggle Button */}
        <div className="absolute bottom-6 left-6 z-[60] pointer-events-auto">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => { setIsSpecChatOpen(!isSpecChatOpen); setUnreadCount(0); }}
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
        <AnimatePresence>
          {isSpecChatOpen && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              className="absolute bottom-24 left-6 z-[60] w-[340px] h-[420px] flex flex-col bg-[#0f172a]/95 backdrop-blur-xl border border-purple-500/30 rounded-2xl shadow-[0_0_40px_rgba(168,85,247,0.15)] overflow-hidden"
            >
              {/* Chat Header */}
              <div className="h-12 bg-purple-500/10 border-b border-purple-500/20 flex items-center justify-between px-4 shrink-0">
                <div className="flex items-center gap-2 text-purple-300 text-xs uppercase tracking-[0.15em] font-bold">
                  <Users className="w-4 h-4" />
                  <span>Spectator Chat</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                  <span className="text-[9px] text-white/30 font-mono">online</span>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-3 space-y-2" ref={specChatScrollRef}>
                {specMessages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-white/20 gap-2">
                    <MessageSquare className="w-8 h-8 opacity-20" />
                    <p className="text-[10px] uppercase tracking-widest">No messages yet...</p>
                  </div>
                ) : (
                  specMessages.map(msg => (
                    <motion.div
                      key={msg.id}
                      initial={{ opacity: 0, x: msg.isMe ? 10 : -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`flex flex-col ${msg.isMe ? 'items-end' : 'items-start'}`}
                    >
                      <div className={`max-w-[85%] ${msg.isMe ? 'items-end' : 'items-start'}`}>
                        <div className="flex items-center gap-2 px-1 mb-0.5">
                          <span className={`text-[10px] font-bold ${msg.isMe ? 'text-purple-300' : 'text-white/60'}`}>{msg.name}</span>
                          <span className="text-[9px] text-white/20">
                            {new Date(msg.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className={`px-3 py-1.5 rounded-lg text-sm leading-relaxed border ${
                          msg.isMe
                            ? 'bg-purple-500/20 text-white border-purple-500/30 rounded-tr-none'
                            : 'bg-white/5 text-white/80 border-white/5 rounded-tl-none'
                        }`}>
                          {msg.text}
                        </div>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>

              {/* Input */}
              <div className="p-3 bg-black/40 border-t border-purple-500/20 shrink-0">
                <form onSubmit={handleSpecChatSend} className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      value={specChatInput}
                      onChange={(e) => setSpecChatInput(e.target.value)}
                      placeholder="Chat with spectators..."
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-purple-500/50 transition-colors"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!specChatInput.trim()}
                    className="w-10 h-10 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 hover:bg-purple-500/30 transition-colors disabled:opacity-30"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Right: Betting Panel */}
        <div className="hidden md:flex w-[380px] shrink-0 h-full border-l border-white/5 z-50 flex-col bg-[#030712]/95 backdrop-blur-xl">

          {/* Panel Header */}
          <div className="h-14 bg-black/40 border-b border-white/5 flex items-center justify-between px-4">
            <div className="flex items-center gap-2 text-gold text-xs uppercase tracking-[0.15em] font-bold">
              <BarChart3 className="w-4 h-4" />
              <span>Betting Terminal</span>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto">

            {/* Live Odds */}
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center gap-1.5 text-[9px] text-white/40 uppercase tracking-widest font-bold mb-3">
                <TrendingUp className="w-3 h-3" /> Live Odds
              </div>
              <div className="grid grid-cols-2 gap-2">
                <GlassCard className="p-3 text-center bg-red-500/5 border-red-500/20">
                  <div className="text-[10px] text-red-400 font-bold uppercase tracking-wider mb-1">Mafia</div>
                  <div className="text-2xl font-mono font-black text-red-400">{mafiaOdds}x</div>
                </GlassCard>
                <GlassCard className="p-3 text-center bg-green-500/5 border-green-500/20">
                  <div className="text-[10px] text-green-400 font-bold uppercase tracking-wider mb-1">Citizens</div>
                  <div className="text-2xl font-mono font-black text-green-400">{citizenOdds}x</div>
                </GlassCard>
              </div>
            </div>

            {/* Place Bet */}
            <div className="p-4 border-b border-white/5 space-y-3">
              <div className="flex items-center gap-1.5 text-[9px] text-white/40 uppercase tracking-widest font-bold">
                <DollarSign className="w-3 h-3" /> Place Bet (USDC)
              </div>

              {/* Bet Type Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowBetTypeDropdown(!showBetTypeDropdown)}
                  className="w-full flex items-center justify-between px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white hover:border-gold/40 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {BET_TYPES.find(b => b.value === selectedBetType)?.icon}
                    <span className="font-medium">{BET_TYPES.find(b => b.value === selectedBetType)?.label}</span>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-white/40 transition-transform ${showBetTypeDropdown ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                  {showBetTypeDropdown && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="absolute top-full left-0 right-0 mt-1 bg-[#1e293b] border border-white/10 rounded-lg overflow-hidden z-50 shadow-2xl"
                    >
                      {BET_TYPES.map(bt => (
                        <button
                          key={bt.value}
                          onClick={() => { setSelectedBetType(bt.value); setBetTarget(''); setShowBetTypeDropdown(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-white/10 transition-colors ${
                            selectedBetType === bt.value ? 'bg-gold/10 text-gold' : 'text-white/80'
                          }`}
                        >
                          {bt.icon}
                          <div>
                            <div className="text-sm font-medium">{bt.label}</div>
                            <div className="text-[10px] text-white/40">{bt.desc}</div>
                          </div>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Target Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowTargetDropdown(!showTargetDropdown)}
                  className="w-full flex items-center justify-between px-3 py-2.5 bg-white/5 border border-white/10 rounded-lg text-sm text-white hover:border-gold/40 transition-colors"
                >
                  <span className={betTarget ? 'font-medium' : 'text-white/30'}>
                    {betTarget || 'Select target...'}
                  </span>
                  <ChevronDown className={`w-4 h-4 text-white/40 transition-transform ${showTargetDropdown ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                  {showTargetDropdown && (
                    <motion.div
                      initial={{ opacity: 0, y: -5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="absolute top-full left-0 right-0 mt-1 bg-[#1e293b] border border-white/10 rounded-lg overflow-hidden z-50 shadow-2xl max-h-[200px] overflow-y-auto"
                    >
                      {getTargetOptions().map(opt => (
                        <button
                          key={opt}
                          onClick={() => { setBetTarget(opt); setShowTargetDropdown(false); }}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-white/10 transition-colors text-sm ${
                            betTarget === opt ? 'bg-gold/10 text-gold' : 'text-white/80'
                          }`}
                        >
                          {selectedBetType !== 'side_win' && (() => {
                            const p = players.find(pl => pl.name === opt);
                            return p?.avatarIndex != null ? (
                              <img src={AVATAR_IMAGES[p.avatarIndex]} alt="" className="w-6 h-6 rounded-full object-cover border border-white/20" />
                            ) : null;
                          })()}
                          {opt}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Amount Input */}
              <div className="space-y-1.5">
                <div className="relative">
                  <Input
                    type="number"
                    placeholder="1.00"
                    value={betAmount}
                    onChange={(e) => setBetAmount(e.target.value)}
                    className="pl-8 pr-20 py-3 bg-white/5 border-white/10 focus:border-gold/50 rounded-lg text-sm !normal-case !tracking-normal !font-mono"
                  />
                  <DollarSign className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-white/30 font-bold">USDC</span>
                </div>
                <div className="flex gap-1.5">
                  {[1, 5, 10, 25].map(amt => (
                    <button
                      key={amt}
                      onClick={() => setBetAmount(amt.toString())}
                      className="flex-1 py-1.5 text-[10px] font-bold text-white/50 bg-white/5 hover:bg-white/10 border border-white/5 hover:border-gold/30 rounded transition-colors"
                    >
                      ${amt}
                    </button>
                  ))}
                  <button
                    onClick={() => setBetAmount(usdcBalance.toFixed(2))}
                    className="flex-1 py-1.5 text-[10px] font-bold text-gold/60 bg-gold/5 hover:bg-gold/10 border border-gold/10 hover:border-gold/30 rounded transition-colors"
                  >
                    MAX
                  </button>
                </div>
              </div>

              {/* Potential Payout */}
              {betAmount && betTarget && odds && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="bg-white/5 rounded-lg px-3 py-2 flex justify-between items-center"
                >
                  <span className="text-[10px] text-white/40 uppercase tracking-wider font-bold">Potential Payout</span>
                  <span className="text-sm font-mono font-bold text-green-400">
                    ${(parseFloat(betAmount || '0') * (betTarget === 'Mafia' ? (1 / odds.mafiaWinProb) : (1 / odds.citizenWinProb))).toFixed(2)} USDC
                  </span>
                </motion.div>
              )}

              <Button
                onClick={handlePlaceBet}
                disabled={!betTarget || !betAmount || parseFloat(betAmount) < 1.0 || parseFloat(betAmount) > usdcBalance}
                size="lg"
                className="w-full"
                icon={<ArrowRight className="w-4 h-4" />}
              >
                {betSuccess ? 'BET PLACED!' : 'PLACE BET'}
              </Button>

              {parseFloat(betAmount || '0') < 1.0 && betAmount !== '' && (
                <p className="text-[10px] text-red-400/80 text-center">Minimum bet: $1.00 USDC</p>
              )}
            </div>

            {/* My Bets */}
            <div className="p-4 border-b border-white/5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5 text-[9px] text-white/40 uppercase tracking-widest font-bold">
                  <Clock className="w-3 h-3" /> My Bets
                </div>
                <span className="text-[9px] text-white/20 font-mono">{usdcBets.length} active</span>
              </div>
              <div className="space-y-2 max-h-[160px] overflow-y-auto">
                {usdcBets.length === 0 ? (
                  <div className="text-center py-4 text-white/20 text-xs">No bets placed yet</div>
                ) : (
                  usdcBets.map(bet => (
                    <motion.div
                      key={bet.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-center justify-between bg-white/5 rounded-lg px-3 py-2 border border-white/5"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-gold/60 uppercase font-bold tracking-wider">
                            {BET_TYPES.find(b => b.value === bet.betType)?.label}
                          </span>
                          <ArrowRight className="w-3 h-3 text-white/20" />
                          <span className="text-xs font-medium text-white">{bet.target}</span>
                        </div>
                        <span className="text-[9px] text-white/30 font-mono">
                          {new Date(bet.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-mono font-bold text-green-400">${bet.amountUSDC.toFixed(2)}</div>
                        <span className={`text-[9px] uppercase font-bold tracking-wider ${
                          bet.status === 'pending' ? 'text-yellow-400' :
                          bet.status === 'won' ? 'text-green-400' : 'text-red-400'
                        }`}>{bet.status}</span>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>

            {/* Chat Log (read-only) */}
            <div className="p-4 border-t border-white/5">
              <div className="flex items-center gap-1.5 text-[9px] text-white/40 uppercase tracking-widest font-bold mb-3">
                <MessageSquare className="w-3 h-3" /> Game Log
              </div>
              <div className="space-y-2 max-h-[200px] overflow-y-auto" ref={scrollRef}>
                {messages.slice(-15).map(msg => (
                  <div key={msg.id} className="text-[11px]">
                    {msg.type === 'system' ? (
                      <span className="text-white/30 italic">{msg.text}</span>
                    ) : msg.type === 'elimination' ? (
                      <span className="text-red-400 flex items-center gap-1">
                        <Skull className="w-3 h-3" /> {msg.text}
                      </span>
                    ) : (
                      <span>
                        <span className="font-bold" style={{ color: msg.color || '#fff' }}>{msg.senderName}: </span>
                        <span className="text-white/70">{msg.text}</span>
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* X402 Branding Footer */}
          <div className="px-4 py-3 border-t border-white/5 bg-black/40 text-center shrink-0">
            <div className="flex items-center justify-center gap-2 text-[9px] text-white/20 font-mono tracking-wider">
              <Zap className="w-3 h-3" />
              Powered by X402 Protocol on Monad
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
