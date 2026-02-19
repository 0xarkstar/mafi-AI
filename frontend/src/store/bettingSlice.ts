import { StateCreator } from 'zustand';
import { Bet, USDCBet, BetType, OddsData } from '../types';
import { sendWS } from '../websocket';
import type { StoreState } from './index';

export interface BettingSlice {
  bets: Bet[];
  usdcBets: USDCBet[];
  usdcBalance: number;
  odds: OddsData | null;

  placeBet: (amount: number, target: 'Mafia' | 'Citizens') => void;
  placeBetUSDC: (betType: BetType, target: string, amount: number) => void;
}

export const createBettingSlice: StateCreator<StoreState, [], [], BettingSlice> = (set) => ({
  bets: [],
  usdcBets: [],
  usdcBalance: 50.0,
  odds: null,

  placeBet: (amount, target) => {
    const newBet: Bet = {
      id: Math.random().toString(36).substr(2, 9),
      amount,
      target,
      status: 'pending',
    };
    set((state) => ({ bets: [...state.bets, newBet] }));
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
    sendWS({
      type: 'place_bet',
      bet_id: newBet.id,
      bet_type: betType,
      target,
      amount_usdc: amount,
    });
  },
});
