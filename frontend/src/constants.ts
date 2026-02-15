import { Player } from './types';

export const AGENTS_DATA: Omit<Player, 'id' | 'role' | 'isDead'>[] = [
  { name: 'Viktor', color: '#3b82f6', isAi: true, avatarIcon: 'Diamond', trait: 'Strategist' },
  { name: 'Luna', color: '#ec4899', isAi: true, avatarIcon: 'Moon', trait: 'Empath' },
  { name: 'Marcus', color: '#ef4444', isAi: true, avatarIcon: 'Flame', trait: 'Intimidator' },
  { name: 'Scarlet', color: '#a855f7', isAi: true, avatarIcon: 'Eye', trait: 'Manipulator' },
  { name: 'Cipher', color: '#22c55e', isAi: true, avatarIcon: 'Hash', trait: 'Observer' },
  { name: 'Blaze', color: '#f97316', isAi: true, avatarIcon: 'Zap', trait: 'Wildcard' },
  { name: 'Sage', color: '#14b8a6', isAi: true, avatarIcon: 'Star', trait: 'Philosopher' },
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
