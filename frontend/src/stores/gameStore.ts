import { create } from 'zustand'
import type { Phase, Player, Vote, Role, PlayerType, ActionRequest, ScreenState } from '../lib/types'
import { AGENTS } from '../lib/constants'

// Module-level timer storage for chat bubbles (not in zustand state)
const chatBubbleTimers = new Map<string, ReturnType<typeof setTimeout>>()

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
  screen: ScreenState
  nickname: string
  avatarIndex: number
  isSpectator: boolean
  activeEmotes: Record<string, { emoji: string; timeout: ReturnType<typeof setTimeout> }>
  chatBubbles: Record<string, string>
  voteCounts: Record<string, number>
  showVoteUI: boolean
  selectedVoteTarget: string | null

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
  setScreen: (screen: ScreenState) => void
  setNickname: (name: string) => void
  setAvatarIndex: (index: number) => void
  setIsSpectator: (isSpectator: boolean) => void
  triggerEmote: (playerId: string, emoji: string) => void
  setChatBubble: (agent: string, message: string) => void
  clearChatBubble: (agent: string) => void
  setVoteCounts: (counts: Record<string, number>) => void
  setShowVoteUI: (show: boolean) => void
  setSelectedVoteTarget: (target: string | null) => void
  resetGame: () => void
}

export const useGameStore = create<GameStore>((set) => ({
  // Initial state
  phase: 'lobby',
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
  screen: 'landing',
  nickname: '',
  avatarIndex: 0,
  isSpectator: false,
  activeEmotes: {},
  chatBubbles: {},
  voteCounts: {},
  showVoteUI: false,
  selectedVoteTarget: null,

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
            avatarIndex: agent.avatarIndex,
          }
          return acc
        },
        {} as Record<string, Player>
      ),
    }),

  setScreen: (screen) => set({ screen }),

  setNickname: (name) => set({ nickname: name }),

  setAvatarIndex: (index) => set({ avatarIndex: index }),

  setIsSpectator: (isSpectator) => set({ isSpectator }),

  triggerEmote: (playerId, emoji) =>
    set((state) => {
      // Clear existing timeout if any
      const existing = state.activeEmotes[playerId]
      if (existing?.timeout) {
        clearTimeout(existing.timeout)
      }

      // Set new emote with auto-clear after 3 seconds
      const timeout = setTimeout(() => {
        set((s) => {
          const { [playerId]: _, ...rest } = s.activeEmotes
          return { activeEmotes: rest }
        })
      }, 3000)

      return {
        activeEmotes: {
          ...state.activeEmotes,
          [playerId]: { emoji, timeout },
        },
      }
    }),

  setChatBubble: (agent, message) => {
    // Clear existing timer for this agent
    const existing = chatBubbleTimers.get(agent)
    if (existing) clearTimeout(existing)

    // Set new timer for auto-clear after 5 seconds
    const timer = setTimeout(() => {
      chatBubbleTimers.delete(agent)
      set((state) => {
        const { [agent]: _, ...rest } = state.chatBubbles
        return { chatBubbles: rest }
      })
    }, 5000)

    chatBubbleTimers.set(agent, timer)

    set((state) => ({
      chatBubbles: { ...state.chatBubbles, [agent]: message },
    }))
  },

  clearChatBubble: (agent) => {
    const existing = chatBubbleTimers.get(agent)
    if (existing) {
      clearTimeout(existing)
      chatBubbleTimers.delete(agent)
    }
    set((state) => {
      const { [agent]: _, ...rest } = state.chatBubbles
      return { chatBubbles: rest }
    })
  },

  setVoteCounts: (counts) => set({ voteCounts: counts }),

  setShowVoteUI: (show) => set({ showVoteUI: show }),

  setSelectedVoteTarget: (target) => set({ selectedVoteTarget: target }),

  resetGame: () => {
    // Clear all bubble timers
    chatBubbleTimers.forEach((timer) => clearTimeout(timer))
    chatBubbleTimers.clear()

    // Clear all emote timeouts
    const current = useGameStore.getState()
    Object.values(current.activeEmotes).forEach(({ timeout }) => clearTimeout(timeout))

    set({
      screen: 'landing',
      phase: 'lobby',
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
      activeEmotes: {},
      chatBubbles: {},
      voteCounts: {},
      showVoteUI: false,
      selectedVoteTarget: null,
    })
  },
}))
