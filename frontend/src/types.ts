export enum ScreenState {
  LANDING = 'LANDING',
  LOBBY = 'LOBBY',
  GAME = 'GAME',
  SPECTATE = 'SPECTATE',
  REVEAL = 'REVEAL',
  GAME_OVER = 'GAME_OVER',
}

export enum GamePhase {
  DAY_DISCUSSION = 'DAY_DISCUSSION',
  DAY_VOTE = 'DAY_VOTE',
  NIGHT = 'NIGHT',
  REVEAL = 'REVEAL',
}

export enum Role {
  MAFIA = 'Mafia',
  CITIZEN = 'Citizen',
  DETECTIVE = 'Detective',
}

export interface Player {
  id: string;
  name: string;
  color: string;
  isAi: boolean;
  role?: Role; // Hidden for others usually
  isDead: boolean;
  avatarIcon: string; // Basic shape name or icon identifier
  avatarIndex?: number; // Index into avatars-grid.png (0-20, 7cols x 3rows)
  trait: string;
}

export interface Message {
  id: string;
  senderId: string; // 'system' or playerId
  senderName: string;
  text: string;
  timestamp: number;
  type: 'chat' | 'system' | 'elimination' | 'game_over';
  color?: string;
}

export interface Bet {
  id: string;
  amount: number;
  target: 'Mafia' | 'Citizens';
  status: 'pending' | 'won' | 'lost';
}

export type BetType = 'side_win' | 'next_elimination' | 'is_mafia' | 'is_ai_or_human';

export interface USDCBet {
  id: string;
  betType: BetType;
  target: string;
  amountUSDC: number;
  timestamp: number;
  status: 'pending' | 'won' | 'lost';
  payout?: number;
}

// WebSocket integration types
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

export interface ActionRequest {
  actionType: string;   // 'statement' | 'vote' | 'night_action'
  prompt: string;
  options: string[];
  timeout: number;
  context: Record<string, unknown>;
}

export interface OddsData {
  mafiaWinProb: number;
  citizenWinProb: number;
  mafiaSuspects: Record<string, number>;
}
