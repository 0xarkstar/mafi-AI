import { Player } from './types';

// Agent data matching backend personalities (src/agents/personalities.py)
// Names MUST match exactly: Viktor, Luna, Rex, Sage, Nova, Iris, Blaze
export const AGENTS_DATA: Omit<Player, 'id' | 'role' | 'isDead'>[] = [
  { name: 'Viktor', color: '#3b82f6', isAi: true, avatarIcon: 'Diamond', trait: 'Strategist' },
  { name: 'Luna', color: '#ec4899', isAi: true, avatarIcon: 'Moon', trait: 'Empath' },
  { name: 'Rex', color: '#ef4444', isAi: true, avatarIcon: 'Flame', trait: 'Bully' },
  { name: 'Sage', color: '#14b8a6', isAi: true, avatarIcon: 'Star', trait: 'Philosopher' },
  { name: 'Nova', color: '#a855f7', isAi: true, avatarIcon: 'Zap', trait: 'Wildcard' },
  { name: 'Iris', color: '#22c55e', isAi: true, avatarIcon: 'Eye', trait: 'Observer' },
  { name: 'Blaze', color: '#f97316', isAi: true, avatarIcon: 'Flame', trait: 'Hothead' },
];

export const PHASE_GRADIENTS = {
  LANDING: 'from-[#030712] via-[#0f172a] to-[#020617]',
  LOBBY: 'from-[#09090b] to-[#18181b]',
  NIGHT: 'from-[#1e1b4b] to-[#020617]',
  DAY_DISCUSSION: 'from-[#451a03] to-[#1c1917]',
  DAY_VOTE: 'from-[#450a0a] to-[#1c1917]',
  REVEAL: 'from-[#4a044e] to-[#0f172a]',
  GAME_OVER: 'from-[#022c22] to-[#0f172a]',
};
