import { create } from 'zustand';
import { createGameSlice, GameSlice } from './gameSlice';
import { createBettingSlice, BettingSlice } from './bettingSlice';
import { createConnectionSlice, ConnectionSlice } from './connectionSlice';
import { createUISlice, UISlice } from './uiSlice';

export type StoreState = GameSlice & BettingSlice & ConnectionSlice & UISlice;

export const useGameStore = create<StoreState>()((...args) => ({
  ...createGameSlice(...args),
  ...createBettingSlice(...args),
  ...createConnectionSlice(...args),
  ...createUISlice(...args),
}));

// Selectors
export const selectAlivePlayers = (state: StoreState) =>
  state.players.filter(p => !p.isDead);

export const selectHumanPlayer = (state: StoreState) =>
  state.players.find(p => p.name === state.playerName);

export const selectIsConnected = (state: StoreState) =>
  state.connectionStatus === 'connected';

export const selectMafiaOdds = (state: StoreState) =>
  state.odds ? (1 / state.odds.mafiaWinProb).toFixed(2) : '—';

export const selectCitizenOdds = (state: StoreState) =>
  state.odds ? (1 / state.odds.citizenWinProb).toFixed(2) : '—';
