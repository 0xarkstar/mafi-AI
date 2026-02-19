import { StateCreator } from 'zustand';
import { ScreenState, GamePhase, Player, Message } from '../types';
import type { ServerEvent } from '../types/events';
import { AGENTS_DATA } from '../constants';
import { disconnectWS, sendWS } from '../websocket';
import { mapPhase, mapRole, mapWinner, buildPlayerFromName } from '../mappers';
import type { StoreState } from './index';

// Module-level timeout tracking (outside Zustand state — must be serializable)
let gameOverTimeoutId: ReturnType<typeof setTimeout> | null = null;
const emoteTimeoutIds = new Map<string, ReturnType<typeof setTimeout>>();

export interface GameSlice {
  screen: ScreenState;
  phase: GamePhase;
  players: Player[];
  messages: Message[];
  round: number;
  winner: 'Mafia' | 'Citizens' | null;
  activeEmotes: Record<string, string>;

  setPhase: (phase: GamePhase) => void;
  addMessage: (msg: Omit<Message, 'id' | 'timestamp'>) => void;
  resetGame: () => void;
  playAgain: () => void;
  triggerReveal: () => void;
  endGame: () => void;
  triggerEmote: (playerId: string, emote: string) => void;
  handleWSEvent: (event: ServerEvent) => void;
}

export const createGameSlice: StateCreator<StoreState, [], [], GameSlice> = (set, get) => ({
  screen: ScreenState.LANDING,
  phase: GamePhase.DAY_DISCUSSION,
  players: [],
  messages: [],
  round: 1,
  winner: null,
  activeEmotes: {},

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
    if (gameOverTimeoutId) { clearTimeout(gameOverTimeoutId); gameOverTimeoutId = null; }
    emoteTimeoutIds.forEach((id) => clearTimeout(id));
    emoteTimeoutIds.clear();
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
      nickname: '',
      currentAction: null,
      odds: null,
      avatarIndex: null,
      specChatMessages: [],
      specChatName: null,
    });
  },

  playAgain: () => {
    if (gameOverTimeoutId) { clearTimeout(gameOverTimeoutId); gameOverTimeoutId = null; }
    const state = get();
    set({
      screen: ScreenState.LOBBY,
      phase: GamePhase.DAY_DISCUSSION,
      players: [],
      messages: [],
      bets: [],
      usdcBets: [],
      round: 1,
      winner: null,
      currentAction: null,
      odds: null,
    });
    sendWS({ type: 'rejoin_lobby', name: state.playerName, avatar_index: state.avatarIndex });
  },

  triggerEmote: (playerId, emote) => {
    set((state) => ({ activeEmotes: { ...state.activeEmotes, [playerId]: emote } }));
    const existing = emoteTimeoutIds.get(playerId);
    if (existing) clearTimeout(existing);
    emoteTimeoutIds.set(playerId, setTimeout(() => {
      emoteTimeoutIds.delete(playerId);
      set((state) => {
        const newEmotes = { ...state.activeEmotes };
        delete newEmotes[playerId];
        return { activeEmotes: newEmotes };
      });
    }, 3000));
  },

  addMessage: (msg) => {
    const newMessage: Message = {
      ...msg,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now(),
    };
    set((state) => ({ messages: [...state.messages, newMessage] }));
  },

  handleWSEvent: (event) => {
    const state = get();

    // Broadcasts come as { event_type, data, game_id, timestamp }
    // Targeted come as { type, action_type, ... }
    const eventType = 'event_type' in event
      ? (event as { event_type: string }).event_type
      : (event as { type: string }).type;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = ('data' in event ? (event as { data: any }).data : event) as any;

    switch (eventType) {
      case 'lobby_status': {
        const rawPlayers = data.players || [];
        const existingPlayers = state.players;

        const players: Player[] = rawPlayers.map((entry: any, idx: number) => {
          const name = typeof entry === 'string' ? entry : entry.name;
          const avatarIdx = typeof entry === 'object' ? entry.avatar_index : undefined;

          const existing = existingPlayers.find((p) => p.name === name);
          if (existing) return existing;

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

          return buildPlayerFromName(name, idx, avatarIdx);
        });

        set({ players });
        break;
      }

      case 'lobby_joined': {
        if (data.success === false) break;
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

        let players = state.players;
        const startingPlayers: { name: string; player_type: string }[] = data.players || [];
        if (startingPlayers.length > 0 && players.length < startingPlayers.length) {
          players = startingPlayers.map((sp, idx) => {
            const existing = state.players.find((p) => p.name === sp.name);
            if (existing) return existing;
            if (sp.name === state.playerName) {
              return {
                id: 'human-1',
                name: sp.name,
                color: '#ffffff',
                isAi: false,
                isDead: false,
                avatarIcon: 'User',
                avatarIndex: state.avatarIndex ?? undefined,
                trait: 'You',
              };
            }
            return buildPlayerFromName(sp.name, idx);
          });
        }

        set({ gameId, screen, players });
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

        let players = state.players;
        if (data.alive_agents) {
          const aliveSet = new Set<string>(data.alive_agents);
          players = state.players.map((p) => ({
            ...p,
            isDead: !aliveSet.has(p.name),
          }));
        }

        const screen = (state.screen === ScreenState.LOBBY || state.screen === ScreenState.LANDING)
          ? (state.isSpectator ? ScreenState.SPECTATE : ScreenState.GAME)
          : state.screen;

        set({
          phase: newPhase,
          round,
          players,
          screen,
          currentAction: null,
        });

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

        if (gameOverTimeoutId) clearTimeout(gameOverTimeoutId);
        gameOverTimeoutId = setTimeout(() => {
          gameOverTimeoutId = null;
          const s = get();
          if (s.winner && s.screen !== ScreenState.REVEAL && s.screen !== ScreenState.GAME_OVER) {
            set({ screen: ScreenState.GAME_OVER });
          }
        }, 15000);
        break;
      }

      case 'action_request': {
        if (state.isSpectator) break;
        const updates: Partial<StoreState> = {
          currentAction: {
            actionType: data.action_type,
            prompt: data.prompt,
            options: data.options || [],
            timeout: data.timeout || 60,
            context: data.context || {},
          },
        };

        const contextRole = data.context?.role;
        if (contextRole) {
          const mapped = mapRole(contextRole);
          updates.players = state.players.map((p) =>
            !p.isAi && !p.role ? { ...p, role: mapped } : p,
          );
        }

        set(updates);
        break;
      }

      case 'balance_update': {
        set({ usdcBalance: data.balance });
        break;
      }

      case 'bet_confirmed': {
        const betId: string = data.bet_id;
        const updates: Partial<StoreState> = {
          usdcBets: get().usdcBets.map((b) =>
            b.id === betId ? { ...b, status: 'pending' as const } : b,
          ),
        };
        if (data.balance != null) {
          updates.usdcBalance = data.balance;
        }
        set(updates);
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

      case 'new_lobby': {
        get().addMessage({
          senderId: 'system',
          senderName: 'System',
          text: 'A new game lobby is open! Click Play Again to join.',
          type: 'system',
        });
        break;
      }

      case 'spec_chat_message': {
        get().addSpecChatMessage({
          name: data.name,
          text: data.text,
          isAi: data.isAi ?? false,
        });
        break;
      }

      case 'spec_chat_joined': {
        get().setSpecChatName(data.name);
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
});
