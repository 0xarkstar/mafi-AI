import { GamePhase, Role, Player } from './types';
import { AGENTS_DATA } from './constants';

const PHASE_MAP: Record<string, GamePhase> = {
  day_discussion: GamePhase.DAY_DISCUSSION,
  day_vote: GamePhase.DAY_VOTE,
  night: GamePhase.NIGHT,
  reveal: GamePhase.REVEAL,
};

export function mapPhase(backend: string): GamePhase {
  return PHASE_MAP[backend] ?? GamePhase.DAY_DISCUSSION;
}

const ROLE_MAP: Record<string, Role> = {
  mafia: Role.MAFIA,
  citizen: Role.CITIZEN,
  detective: Role.DETECTIVE,
};

export function mapRole(backend: string): Role {
  return ROLE_MAP[backend] ?? Role.CITIZEN;
}

export function mapWinner(backend: string): 'Mafia' | 'Citizens' {
  return backend === 'mafia' ? 'Mafia' : 'Citizens';
}

/**
 * Build a Player object from a backend name.
 * Tries to match against AGENTS_DATA for color/trait/icon.
 * Falls back to generic defaults for unknown names (human players).
 */
export function buildPlayerFromName(name: string, index: number): Player {
  const agentData = AGENTS_DATA.find((a) => a.name === name);

  if (agentData) {
    return {
      id: `ai-${index}`,
      name: agentData.name,
      color: agentData.color,
      isAi: true,
      isDead: false,
      avatarIcon: agentData.avatarIcon,
      avatarIndex: index % 8,
      trait: agentData.trait,
    };
  }

  // Unknown name = likely a human player
  return {
    id: `human-${index}`,
    name,
    color: '#ffffff',
    isAi: false,
    isDead: false,
    avatarIcon: 'User',
    trait: 'Player',
  };
}
