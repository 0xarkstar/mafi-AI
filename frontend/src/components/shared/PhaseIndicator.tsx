import { GamePhase } from '../../types';
import { Sun, Moon } from 'lucide-react';

interface PhaseIndicatorProps {
  phase: GamePhase;
  round: number;
  timeLeft: number;
}

export const PhaseIndicator = ({ phase, round, timeLeft }: PhaseIndicatorProps) => (
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
);
