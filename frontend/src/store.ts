import { create } from 'zustand';
import { ScreenState, GamePhase, Player, Message, Bet, USDCBet, BetType, ConnectionStatus, ActionRequest, OddsData } from './types';
import { AGENTS_DATA } from './constants';
import { connectWS, sendWS, disconnectWS } from './websocket';
import { mapPhase, mapRole, mapWinner, buildPlayerFromName } from './mappers';

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

  // WebSocket state
  connectionStatus: ConnectionStatus;
  gameId: string | null;
  playerName: string;
  currentAction: ActionRequest | null;
  odds: OddsData | null;
  avatarIndex: number | null;

  // Actions
  connectWallet: () => Promise<void>;
  connectAndJoin: (nickname: string, avatarIndex: number) => void;
  joinAsSpectator: () => void;
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  placeBet: (amount: number, target: 'Mafia' | 'Citizens') => void;
  placeBetUSDC: (betType: BetType, target: string, amount: number) => void;
  submitActionResponse: (response: string) => void;
  setPhase: (phase: GamePhase) => void;
  resetGame: () => void;
  triggerReveal: () => void;
  endGame: () => void;
  triggerEmote: (playerId: string, emote: string) => void;
  handleWSEvent: (event: any) => void;
}

export const useGameStore = create<GameState>((set, get) => ({
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

  // WebSocket state
  connectionStatus: 'disconnected',
  gameId: null,
  playerName: '',
  currentAction: null,
  odds: null,
  avatarIndex: null,

  connectWallet: async () => {
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
        await new Promise((resolve) => setTimeout(resolve, 800));
        set({ walletConnected: true, walletAddress: '0x71C...9A21' });
      }
    } else {
      await new Promise((resolve) => setTimeout(resolve, 800));
      set({ walletConnected: true, walletAddress: '0x71C...9A21' });
    }
  },

  connectAndJoin: (nickname, avatarIndex) => {
    set({
      connectionStatus: 'connecting',
      playerName: nickname,
      nickname,
      avatarIndex,
    });

    connectWS(
      // onMessage
      (data) => get().handleWSEvent(data),
      // onStatus
      (status) => set({ connectionStatus: status }),
      // onOpen — send join_lobby when connected
      () => {
        sendWS({ type: 'join_lobby', name: nickname });
      },
    );
  },

  joinAsSpectator: () => {
    set({
      isSpectator: true,
      connectionStatus: 'connecting',
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

    connectWS(
      (data) => get().handleWSEvent(data),
      (status) => set({ connectionStatus: status }),
      null, // no onOpen callback — spectators don't join lobby
    );
  },

  handleWSEvent: (event) => {
    const state = get();

    // Broadcasts come as { event_type, data, game_id, timestamp }
    // Targeted come as { type, action_type, ... }
    const eventType = event.event_type || event.type;
    const data = event.data || event;

    switch (eventType) {
      case 'lobby_status': {
        const names: string[] = data.players || [];
        const existingPlayers = state.players;

        // Build player list, preserving existing player objects when possible
        const players: Player[] = names.map((name, idx) => {
          const existing = existingPlayers.find((p) => p.name === name);
          if (existing) return existing;

          // Check if this is the human player
          if (name === state.playerName) {
            return {
              id: 'human-1',
              name,
              color: '#ffffff',
              isAi: false,
              isDead: false,
              avatarIcon: 'User',
              avatarIndex: state.avatarIndex ?? undefined,
              trait: 'You',
            };
          }

          return buildPlayerFromName(name, idx);
        });

        set({ players });
        break;
      }

      case 'lobby_joined': {
        if (data.success === false) break; // server rejected join
        set({
          gameId: data.game_id || null,
          screen: ScreenState.LOBBY,
          connectionStatus: 'connected',
        });
        break;
      }

      case 'game_starting': {
        const gameId = data.game_id || state.gameId;
        const screen = state.screen === ScreenState.LOBBY || state.screen === ScreenState.LANDING
          ? (state.isSpectator ? ScreenState.SPECTATE : ScreenState.GAME)
          : state.screen;
        set({ gameId, screen });
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: 'Game is starting!',
          type: 'system',
        });
        break;
      }

      case 'phase_change': {
        const newPhase = mapPhase(data.phase);
        const round = data.round ?? state.round;

        // Update alive/dead from alive_agents if provided
        let players = state.players;
        if (data.alive_agents) {
          const aliveSet = new Set<string>(data.alive_agents);
          players = state.players.map((p) => ({
            ...p,
            isDead: !aliveSet.has(p.name),
          }));
        }

        // If we were in LOBBY and phase changed, transition to GAME screen
        const screen = (state.screen === ScreenState.LOBBY || state.screen === ScreenState.LANDING)
          ? (state.isSpectator ? ScreenState.SPECTATE : ScreenState.GAME)
          : state.screen;

        set({
          phase: newPhase,
          round,
          players,
          screen,
          currentAction: null, // clear any pending action on phase change
        });

        // Add a system message for phase transitions
        const phaseLabel = data.phase?.replace(/_/g, ' ').toUpperCase() || newPhase;
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `Phase: ${phaseLabel} — Round ${round}`,
          type: 'system',
        });
        break;
      }

      case 'agent_message': {
        const agentName: string = data.agent;
        const agentData = AGENTS_DATA.find((a) => a.name === agentName);
        const player = state.players.find((p) => p.name === agentName);

        get().addMessage({
          senderId: player?.id || agentName,
          senderName: agentName,
          text: data.message,
          type: 'chat',
          color: agentData?.color || player?.color || '#888',
        });
        break;
      }

      case 'vote_cast': {
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `${data.voter} voted for ${data.target}`,
          type: 'system',
        });
        break;
      }

      case 'elimination': {
        const elimName: string = data.agent;
        const reason = data.reason === 'killed_at_night' ? 'was killed during the night' : 'was voted out';
        const roleText = data.role ? ` (${data.role})` : '';

        // Mark player as dead
        set((s) => ({
          players: s.players.map((p) =>
            p.name === elimName ? { ...p, isDead: true } : p,
          ),
        }));

        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `${elimName}${roleText} ${reason}.`,
          type: 'elimination',
        });
        break;
      }

      case 'odds_update': {
        set({
          odds: {
            mafiaWinProb: data.mafia_win_prob,
            citizenWinProb: data.citizen_win_prob,
            mafiaSuspects: data.mafia_suspects || {},
          },
        });
        break;
      }

      case 'identity_reveal': {
        const revealName: string = data.player_name || data.name;
        const role = mapRole(data.role);
        const playerType: string = data.player_type;

        set((s) => ({
          players: s.players.map((p) =>
            p.name === revealName
              ? { ...p, role, isAi: playerType !== 'human' && playerType !== 'agent_human' }
              : p,
          ),
        }));

        // When all revealed, transition to reveal screen
        if (data.all_revealed) {
          set({ screen: ScreenState.REVEAL });
        }
        break;
      }

      case 'game_over': {
        const winner = mapWinner(data.winner);
        set({ winner });

        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `Game Over! ${winner} win!`,
          type: 'game_over',
        });

        // Safety: if no identity_reveal transitions to REVEAL within 15s, go to GAME_OVER directly
        setTimeout(() => {
          const s = get();
          if (s.winner && s.screen !== ScreenState.REVEAL && s.screen !== ScreenState.GAME_OVER) {
            set({ screen: ScreenState.GAME_OVER });
          }
        }, 15000);
        break;
      }

      case 'action_request': {
        if (state.isSpectator) break;
        set({
          currentAction: {
            actionType: data.action_type,
            prompt: data.prompt,
            options: data.options || [],
            timeout: data.timeout || 60,
            context: data.context || {},
          },
        });
        break;
      }

      case 'bet_confirmed': {
        // Update the matching bet status to confirmed
        const betId: string = data.bet_id;
        set((s) => ({
          usdcBets: s.usdcBets.map((b) =>
            b.id === betId ? { ...b, status: 'pending' as const } : b,
          ),
        }));
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `Bet confirmed: $${data.amount_usdc || ''} USDC on ${data.target || 'unknown'}`,
          type: 'system',
        });
        break;
      }

      case 'bet_rejected': {
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `Bet rejected: ${data.reason || 'Unknown error'}`,
          type: 'system',
        });
        break;
      }

      case 'usdc_settlement': {
        // Update bet status based on settlement
        const settledBetId: string = data.bet_id;
        const won: boolean = data.won ?? false;
        const payout: number = data.payout ?? 0;
        set((s) => ({
          usdcBets: s.usdcBets.map((b) =>
            b.id === settledBetId
              ? { ...b, status: won ? ('won' as const) : ('lost' as const), payout }
              : b,
          ),
          usdcBalance: won ? s.usdcBalance + payout : s.usdcBalance,
        }));
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: won ? `You won $${payout.toFixed(2)} USDC!` : 'Bet lost. Better luck next time!',
          type: 'system',
        });
        break;
      }

      case 'error': {
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: `Error: ${data.message || 'Unknown error'}`,
          type: 'system',
        });
        break;
      }
    }
  },

  submitActionResponse: (response) => {
    const state = get();
    sendWS({
      type: 'action_response',
      player_name: state.playerName,
      response,
    });
    set({ currentAction: null });
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
    set({ screen: ScreenState.GAME_OVER });
  },

  resetGame: () => {
    disconnectWS();
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
      connectionStatus: 'disconnected',
      gameId: null,
      playerName: '',
      currentAction: null,
      odds: null,
      avatarIndex: null,
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
