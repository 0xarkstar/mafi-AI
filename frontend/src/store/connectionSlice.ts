import { StateCreator } from 'zustand';
import { ConnectionStatus, ScreenState, GamePhase } from '../types';
import { connectWS, sendWS, disconnectWS } from '../websocket';
import type { StoreState } from './index';

export interface ConnectionSlice {
  connectionStatus: ConnectionStatus;
  gameId: string | null;
  playerName: string;
  avatarIndex: number | null;
  walletConnected: boolean;
  walletAddress: string;

  setWalletConnected: (address: string) => void;
  disconnectWallet: () => void;
  connectAndJoin: (nickname: string, avatarIndex: number) => void;
  joinAsSpectator: () => void;
  submitActionResponse: (response: string) => void;
}

export const createConnectionSlice: StateCreator<StoreState, [], [], ConnectionSlice> = (set, get) => ({
  connectionStatus: 'disconnected',
  gameId: null,
  playerName: '',
  avatarIndex: null,
  walletConnected: false,
  walletAddress: '',

  setWalletConnected: (address) => {
    set({ walletConnected: true, walletAddress: address });
  },

  disconnectWallet: () => {
    set({ walletConnected: false, walletAddress: '' });
  },

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
        sendWS({ type: 'join_lobby', name: nickname, avatar_index: avatarIndex, wallet_address: get().walletAddress || undefined });
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
      () => {
        sendWS({ type: 'join_spec_chat' });
        const walletAddr = get().walletAddress;
        if (walletAddr) {
          sendWS({ type: 'register_wallet', wallet_address: walletAddr });
        }
      },
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
