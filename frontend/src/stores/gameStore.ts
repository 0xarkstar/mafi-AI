import { create } from 'zustand'
import type { Phase, Player, Vote, Role, PlayerType, ActionRequest } from '../lib/types'
import { AGENTS } from '../lib/constants'

interface GameStore {
  // State
  phase: Phase
  round: number
  players: Record<string, Player>
  votes: Vote[]
  winner: string | null
  isPlayer: boolean
  myPlayerName: string | null
  lobbyPlayers: string[]
  lobbyCount: number
  lobbyReady: boolean
  actionRequest: ActionRequest | null

  // Actions
  setPhase: (phase: Phase, round: number) => void
  setPlayerAlive: (name: string, alive: boolean) => void
  setPlayerRole: (name: string, role: Role) => void
  setPlayerSpeaking: (name: string, speaking: boolean) => void
  setPlayerType: (name: string, playerType: PlayerType) => void
  addVote: (voter: string, target: string) => void
  clearVotes: () => void
  setWinner: (winner: string) => void
  setIsPlayer: (isPlayer: boolean, name: string | null) => void
  updateLobby: (players: string[], count: number, ready: boolean) => void
  setActionRequest: (req: ActionRequest | null) => void
  initPlayers: () => void
}

export const useGameStore = create<GameStore>((set) => ({
  // Initial state
  phase: 'landing',
  round: 0,
  players: {},
  votes: [],
  winner: null,
  isPlayer: false,
  myPlayerName: null,
  lobbyPlayers: [],
  lobbyCount: 0,
  lobbyReady: false,
  actionRequest: null,

  // Actions
  setPhase: (phase, round) => set({ phase, round }),

  setPlayerAlive: (name, alive) =>
    set((state) => {
      const player = state.players[name]
      if (!player) return {}
      return {
        players: {
          ...state.players,
          [name]: { ...player, isAlive: alive },
        },
      }
    }),

  setPlayerRole: (name, role) =>
    set((state) => {
      const player = state.players[name]
      if (!player) return {}
      return {
        players: {
          ...state.players,
          [name]: { ...player, role },
        },
      }
    }),

  setPlayerSpeaking: (name, speaking) =>
    set((state) => {
      const player = state.players[name]
      if (!player) return {}
      return {
        players: {
          ...state.players,
          [name]: { ...player, isSpeaking: speaking },
        },
      }
    }),

  setPlayerType: (name, playerType) =>
    set((state) => {
      const player = state.players[name]
      if (!player) return {}
      return {
        players: {
          ...state.players,
          [name]: { ...player, playerType },
        },
      }
    }),

  addVote: (voter, target) =>
    set((state) => ({
      votes: [...state.votes, { voter, target }],
    })),

  clearVotes: () => set({ votes: [] }),

  setWinner: (winner) => set({ winner }),

  setIsPlayer: (isPlayer, name) => set({ isPlayer, myPlayerName: name }),

  updateLobby: (players, count, ready) =>
    set({ lobbyPlayers: players, lobbyCount: count, lobbyReady: ready }),

  setActionRequest: (req) => set({ actionRequest: req }),

  initPlayers: () =>
    set({
      players: AGENTS.reduce(
        (acc, agent) => {
          acc[agent.name] = {
            name: agent.name,
            color: agent.color,
            trait: agent.trait,
            isAlive: true,
            role: null,
            playerType: null,
            isSpeaking: false,
          }
          return acc
        },
        {} as Record<string, Player>
      ),
    }),
}))
