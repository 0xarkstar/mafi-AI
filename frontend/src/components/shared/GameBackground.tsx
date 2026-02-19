import type React from 'react';
import { GamePhase } from '../../types';

interface GameBackgroundProps {
  phase: GamePhase;
  children: React.ReactNode;
}

export const GameBackground = ({ phase, children }: GameBackgroundProps) => (
  <div className="h-screen w-full flex flex-col overflow-hidden relative bg-[#050505]">
    <img
      src="/images/game-bg.png"
      alt=""
      className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-0' : 'opacity-100'}`}
    />
    <img
      src="/images/game-bg-night.png"
      alt=""
      className={`absolute inset-0 w-full h-full object-cover z-0 pointer-events-none transition-opacity duration-[2000ms] ${phase === GamePhase.NIGHT ? 'opacity-100' : 'opacity-0'}`}
    />
    <div
      className={`absolute inset-0 transition-all duration-[2000ms] z-[1] pointer-events-none
        ${phase === GamePhase.NIGHT ? 'bg-[#0a0e1f]/60' :
          phase === GamePhase.DAY_VOTE ? 'bg-[#1a0505]/70' :
          'bg-[#0a0a05]/50'}`}
    />
    {children}
  </div>
);
