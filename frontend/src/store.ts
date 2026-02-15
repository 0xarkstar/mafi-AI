import { create } from 'zustand';
import { ScreenState, GamePhase, Player, Message, Bet, Role, USDCBet, BetType } from './types';
import { AGENTS_DATA } from './constants';

interface GameState {
  screen: ScreenState;
  phase: GamePhase;
  walletConnected: boolean;
  walletAddress: string | null;
  balance: number;
  nickname: string;
  players: Player[];
  messages: Message[];
  bets: Bet[];
  usdcBets: USDCBet[];
  usdcBalance: number;
  round: number;
  winner: 'Mafia' | 'Citizens' | null;
  activeEmotes: Record<string, string>;
  isSpectator: boolean;

  // Actions
  connectWallet: () => Promise<void>;
  joinGame: (nickname: string, avatarIndex: number) => void;
  joinAsSpectator: () => void;
  startGame: () => void;
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  placeBet: (amount: number, target: 'Mafia' | 'Citizens') => void;
  placeBetUSDC: (betType: BetType, target: string, amount: number) => void;
  setPhase: (phase: GamePhase) => void;
  resetGame: () => void;
  triggerReveal: () => void;
  endGame: () => void;
  triggerEmote: (playerId: string, emote: string) => void;
}

export const useGameStore = create<GameState>((set) => ({
  screen: ScreenState.LANDING,
  phase: GamePhase.DAY_DISCUSSION,
  walletConnected: false,
  walletAddress: null,
  balance: 1000,
  nickname: '',
  players: [],
  messages: [],
  bets: [],
  usdcBets: [],
  usdcBalance: 50.0,
  round: 1,
  winner: null,
  activeEmotes: {},
  isSpectator: false,

  connectWallet: async () => {
    // Real MetaMask integration
    if (typeof window !== 'undefined' && (window as any).ethereum) {
      try {
        const { ethers } = await import('ethers');
        const provider = new ethers.BrowserProvider((window as any).ethereum);
        const accounts = await provider.send('eth_requestAccounts', []);
        const address = accounts[0] as string;
        set({
          walletConnected: true,
          walletAddress: `${address.slice(0, 6)}...${address.slice(-4)}`,
        });
      } catch {
        // Fallback on error
        await new Promise((resolve) => setTimeout(resolve, 800));
        set({ walletConnected: true, walletAddress: '0x71C...9A21' });
      }
    } else {
      // Fallback: simulate for demo when no MetaMask
      await new Promise((resolve) => setTimeout(resolve, 800));
      set({ walletConnected: true, walletAddress: '0x71C...9A21' });
    }
  },

  joinGame: (nickname, avatarIndex) => {
    // 2. Prepare AI agents data
    const shuffledAgents = [...AGENTS_DATA].sort(() => 0.5 - Math.random()).slice(0, 6);

    // Assign roles randomly among ALL 7 players (including human)
    const allRoles = [Role.MAFIA, Role.MAFIA, Role.DETECTIVE, Role.CITIZEN, Role.CITIZEN, Role.CITIZEN, Role.CITIZEN];
    const shuffledRoles = allRoles.sort(() => 0.5 - Math.random());

    // Assign avatar images to AI players (excluding the human's chosen avatar)
    const availableAvatars = Array.from({ length: 8 }, (_, i) => i).filter(i => i !== avatarIndex);
    const shuffledAvatars = availableAvatars.sort(() => 0.5 - Math.random());

    // 1. Create human player with random role
    const human: Player = {
      id: 'human-1',
      name: nickname,
      color: '#ffffff',
      isAi: false,
      role: shuffledRoles[0]!,
      isDead: false,
      avatarIcon: 'User',
      avatarIndex,
      trait: 'You',
    };

    const aiPlayers: Player[] = shuffledAgents.map((agent, idx) => ({
      ...agent,
      id: `ai-${idx}`,
      role: shuffledRoles[idx + 1]!,
      isDead: false,
      avatarIndex: shuffledAvatars[idx],
    }));

    // 3. Set initial state with ONLY HUMAN
    set({
      nickname,
      players: [human],
      screen: ScreenState.LOBBY,
    });

    // 4. Simulate sequential joining for visual effect
    let currentIndex = 0;
    const joinInterval = setInterval(() => {
      if (currentIndex >= aiPlayers.length) {
        clearInterval(joinInterval);
        return;
      }

      const nextPlayer = aiPlayers[currentIndex]!;
      set((state) => ({ players: [...state.players, nextPlayer] }));
      currentIndex++;
    }, 800);
  },

  joinAsSpectator: () => {
    // Create a full AI-only game for spectating
    const shuffledAgents = [...AGENTS_DATA].sort(() => 0.5 - Math.random()).slice(0, 7);
    const allRoles = [Role.MAFIA, Role.MAFIA, Role.DETECTIVE, Role.CITIZEN, Role.CITIZEN, Role.CITIZEN, Role.CITIZEN];
    const shuffledRoles = allRoles.sort(() => 0.5 - Math.random());
    const shuffledAvatars = Array.from({ length: 8 }, (_, i) => i).sort(() => 0.5 - Math.random());

    const aiPlayers: Player[] = shuffledAgents.map((agent, idx) => ({
      ...agent,
      id: `ai-${idx}`,
      role: shuffledRoles[idx]!,
      isDead: false,
      avatarIndex: shuffledAvatars[idx],
    }));

    set({
      isSpectator: true,
      players: aiPlayers,
      screen: ScreenState.SPECTATE,
      phase: GamePhase.DAY_DISCUSSION,
      round: 1,
      messages: [{
        id: 'sys-start',
        senderId: 'system',
        senderName: 'System',
        text: 'You are spectating. Place your bets!',
        timestamp: Date.now(),
        type: 'system',
      }],
    });
  },

  startGame: () => {
    set({
      screen: ScreenState.GAME,
      phase: GamePhase.DAY_DISCUSSION,
      round: 1,
      messages: [{
        id: 'sys-start',
        senderId: 'system',
        senderName: 'System',
        text: 'Welcome to Mafia AI. Can you tell who is real?',
        timestamp: Date.now(),
        type: 'system',
      }],
    });
  },

  addMessage: (msg) => {
    const newMessage: Message = {
      ...msg,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now(),
    };
    set((state) => ({ messages: [...state.messages, newMessage] }));
  },

  placeBet: (amount, target) => {
    const newBet: Bet = {
      id: Math.random().toString(36).substr(2, 9),
      amount,
      target,
      status: 'pending',
    };
    set((state) => ({
      bets: [...state.bets, newBet],
      balance: state.balance - amount,
    }));
  },

  placeBetUSDC: (betType, target, amount) => {
    const newBet: USDCBet = {
      id: Math.random().toString(36).substr(2, 9),
      betType,
      target,
      amountUSDC: amount,
      timestamp: Date.now(),
      status: 'pending',
    };
    set((state) => ({
      usdcBets: [...state.usdcBets, newBet],
      usdcBalance: state.usdcBalance - amount,
    }));
  },

  setPhase: (phase) => {
    set({ phase });
  },

  triggerReveal: () => {
    set({
      screen: ScreenState.REVEAL,
      phase: GamePhase.REVEAL,
    });
  },

  endGame: () => {
    const winner = Math.random() > 0.5 ? 'Mafia' : 'Citizens';
    set({
      screen: ScreenState.GAME_OVER,
      winner,
    });
  },

  resetGame: () => {
    set({
      screen: ScreenState.LANDING,
      phase: GamePhase.DAY_DISCUSSION,
      players: [],
      messages: [],
      bets: [],
      usdcBets: [],
      usdcBalance: 50.0,
      round: 1,
      winner: null,
      activeEmotes: {},
      isSpectator: false,
    });
  },

  triggerEmote: (playerId, emote) => {
    set((state) => ({ activeEmotes: { ...state.activeEmotes, [playerId]: emote } }));
    setTimeout(() => {
      set((state) => {
        const newEmotes = { ...state.activeEmotes };
        delete newEmotes[playerId];
        return { activeEmotes: newEmotes };
      });
    }, 3000);
  },
}));
