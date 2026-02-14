import { useState, useEffect } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { usePhaseTheme } from './hooks/usePhaseTheme'
import { useGameState } from './hooks/useGameState'
import { useGameStore } from './stores/gameStore'
import { LobbyScreen } from './components/lobby/LobbyScreen'
import { GameLayout } from './components/layout/GameLayout'
import { PhaseOverlay } from './components/game/PhaseOverlay'
import { EliminationModal } from './components/game/EliminationModal'
import { GameOverScreen } from './components/game/GameOverScreen'
import { ActionPanel } from './components/game/ActionPanel'
import { TxToast } from './components/wallet/TxToast'
import type { Role } from './lib/types'

interface EliminationData {
  playerName: string
  role: Role
  reason: 'killed_at_night' | 'voted_out'
}

export default function App() {
  const { send } = useWebSocket()
  usePhaseTheme()
  const { phase, winner, actionRequest } = useGameState()

  const [eliminationData, setEliminationData] = useState<EliminationData | null>(null)

  // Listen for elimination events from WebSocket
  useEffect(() => {
    // This would ideally be in useWebSocket, but for now we'll handle it here
    // In production, you'd extract the elimination event and pass it up
    // For now, we'll just clear it after a delay if it's set
    if (eliminationData) {
      const timer = setTimeout(() => setEliminationData(null), 3500)
      return () => clearTimeout(timer)
    }
  }, [eliminationData])

  const handleJoin = (name: string) => {
    send({ type: 'join_lobby', name })
  }

  const handleActionSubmit = (response: string) => {
    if (!actionRequest) return
    const { myPlayerName } = useGameStore.getState()
    send({
      type: 'action_response',
      player_name: myPlayerName,
      response,
    })
  }

  return (
    <>
      {phase === 'lobby' && <LobbyScreen onJoin={handleJoin} />}

      {phase !== 'lobby' && (
        <>
          <GameLayout />
          {actionRequest && <ActionPanel onSubmit={handleActionSubmit} />}
        </>
      )}

      <PhaseOverlay />

      {eliminationData && (
        <EliminationModal
          playerName={eliminationData.playerName}
          role={eliminationData.role}
          reason={eliminationData.reason}
          onClose={() => setEliminationData(null)}
        />
      )}

      {winner && <GameOverScreen winner={winner} />}

      <TxToast />
    </>
  )
}
