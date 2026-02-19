import { StateCreator } from 'zustand';
import { ConnectionStatus, ScreenState, GamePhase } from '../types';
import { connectWS, sendWS, disconnectWS } from '../websocket';
import type { StoreState } from './index';

export interface ConnectionSlice {
  connectionStatus: ConnectionStatus;
  gameId: string | null;
  playerName: string;
  avatarIndex: number | null;

  connectAndJoin: (nickname: string, avatarIndex: number) => void;
  joinAsSpectator: () => void;
  submitActionResponse: (response: string) => void;
}

export const createConnectionSlice: StateCreator<StoreState, [], [], ConnectionSlice> = (set, get) => ({
  connectionStatus: 'disconnected',
  gameId: null,
  playerName: '',
  avatarIndex: null,

  connectAndJoin: (nickname, avatarIndex) => {
    set({
      connectionStatus: 'connecting',
      playerName: nickname,
      nickname,
      avatarIndex,
    });
    connectWS(
      (data) => get().handleWSEvent(data),
      (status) => set({ connectionStatus: status }),
      () => {
        sendWS({ type: 'join_lobby', name: nickname, avatar_index: avatarIndex });
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
      null,
    );
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
});

// Keep disconnectWS accessible from outside slices (used in resetGame)
export { disconnectWS };
