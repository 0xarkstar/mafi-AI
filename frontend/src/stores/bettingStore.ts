import { create } from 'zustand'
import type { Bet, OddsBoard } from '../lib/types'

interface BettingStore {
  bets: Bet[]
  odds: OddsBoard
  balance: number

  addBet: (bet: Bet) => void
  updateBetStatus: (betId: string, status: Bet['status']) => void
  setOdds: (odds: Partial<OddsBoard>) => void
  setBalance: (balance: number) => void
}

export const useBettingStore = create<BettingStore>((set) => ({
  bets: [],
  odds: {
    mafiaWinProb: 0.5,
    citizenWinProb: 0.5,
    mafiaSuspects: {},
  },
  balance: 1000,

  addBet: (bet) =>
    set((state) => ({
      bets: [...state.bets, bet],
    })),

  updateBetStatus: (betId, status) =>
    set((state) => ({
      bets: state.bets.map((bet) => (bet.id === betId ? { ...bet, status } : bet)),
    })),

  setOdds: (odds) =>
    set((state) => ({
      odds: { ...state.odds, ...odds },
    })),

  setBalance: (balance) => set({ balance }),
}))
