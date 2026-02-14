import { useShallow } from 'zustand/react/shallow'
import { useGameStore } from '../stores/gameStore'

export function useGameState() {
  return useGameStore(
    useShallow((s) => ({
      phase: s.phase,
      round: s.round,
      players: s.players,
      votes: s.votes,
      winner: s.winner,
      isPlayer: s.isPlayer,
      myPlayerName: s.myPlayerName,
      lobbyPlayers: s.lobbyPlayers,
      lobbyCount: s.lobbyCount,
      lobbyReady: s.lobbyReady,
      actionRequest: s.actionRequest,
    })),
  )
}
