import type React from 'react';

interface GameHeaderProps {
  left?: React.ReactNode;
  center?: React.ReactNode;
  right?: React.ReactNode;
}

export const GameHeader = ({ left, center, right }: GameHeaderProps) => (
  <header className="h-16 px-6 flex items-center justify-between bg-[#030712]/80 backdrop-blur-md border-b border-white/5 z-[10] shrink-0 relative">
    <div className="flex items-center gap-3">{left}</div>
    {center}
    <div className="flex items-center gap-4">{right}</div>
  </header>
);
