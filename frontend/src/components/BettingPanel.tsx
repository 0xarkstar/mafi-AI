import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BetType, OddsData, Player, USDCBet, Message } from '../types';
import { AVATAR_IMAGES } from '../constants';
import { GlassCard, Button, Input } from './UIComponents';
import { TIMING } from '../constants/timing';
import {
  TrendingUp, DollarSign, ArrowRight, Clock, Zap,
  BarChart3, MessageSquare, Skull, ChevronDown, Eye, Target, Users,
} from 'lucide-react';

const BET_TYPES: { value: BetType; label: string; desc: string; icon: React.ReactNode }[] = [
  { value: 'side_win', label: 'Side Win', desc: 'Who wins the game?', icon: <Users className="w-4 h-4" /> },
  { value: 'next_elimination', label: 'Next Out', desc: 'Who gets eliminated next?', icon: <Target className="w-4 h-4" /> },
  { value: 'is_mafia', label: 'Is Mafia?', desc: 'Is this player Mafia?', icon: <Eye className="w-4 h-4" /> },
  { value: 'is_ai_or_human', label: 'AI or Human?', desc: 'Is this player AI or Human?', icon: <Zap className="w-4 h-4" /> },
];

interface BettingPanelProps {
  players: Player[];
  odds: OddsData | null;
  usdcBalance: number;
  usdcBets: USDCBet[];
  messages: Message[];
  placeBetUSDC: (betType: BetType, target: string, amount: number) => void;
}

export const BettingPanel = ({ players, odds, usdcBalance, usdcBets, messages, placeBetUSDC }: BettingPanelProps) => {
  const [selectedBetType, setSelectedBetType] = useState<BetType>('side_win');
  const [betTarget, setBetTarget] = useState('');
  const [betAmount, setBetAmount] = useState('');
  const [showBetTypeDropdown, setShowBetTypeDropdown] = useState(false);
  const [showTargetDropdown, setShowTargetDropdown] = useState(false);
  const [betSuccess, setBetSuccess] = useState(false);
  const betSuccessTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const mafiaOdds = odds ? (1 / odds.mafiaWinProb).toFixed(2) : '—';
  const citizenOdds = odds ? (1 / odds.citizenWinProb).toFixed(2) : '—';

  const getTargetOptions = () => {
    if (selectedBetType === 'side_win') return ['Mafia', 'Citizens'];
    return players.filter(p => !p.isDead).map(p => p.name);
  };

  const handlePlaceBet = () => {
    const amt = parseFloat(betAmount);
    const validTargets = getTargetOptions();
    if (!betTarget || !validTargets.includes(betTarget) || isNaN(amt) || amt < 1.0 || amt > usdcBalance) return;
    placeBetUSDC(selectedBetType, betTarget, amt);
    setBetSuccess(true);
    setBetAmount('');
    setBetTarget('');
    if (betSuccessTimerRef.current) clearTimeout(betSuccessTimerRef.current);
    betSuccessTimerRef.current = setTimeout(() => setBetSuccess(false), TIMING.BET_SUCCESS_DURATION);
  };

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      if (betSuccessTimerRef.current) clearTimeout(betSuccessTimerRef.current);
    };
  }, []);

  return (
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
  );
};
