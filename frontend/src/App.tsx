import { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { useGameStore } from './stores/gameStore'
import { useWebSocket } from './hooks/useWebSocket'
import { usePhaseTheme } from './hooks/usePhaseTheme'
import { LobbyScreen } from './components/lobby/LobbyScreen'
import { LandingScreen } from './screens/LandingScreen'
import { SpectatorScreen } from './screens/SpectatorScreen'
import { RevealScreen } from './screens/RevealScreen'
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

// Wrapper for Lobby Screen with WebSocket
function LobbyScreenWrapper() {
  const { send } = useWebSocket()

  const handleJoin = (name: string) => {
    send({ type: 'join_lobby', name })
  }

  return <LobbyScreen onJoin={handleJoin} />
}

// Wrapper for Game Screen with WebSocket
function GameScreenWrapper() {
  const { send } = useWebSocket()
  const actionRequest = useGameStore((s) => s.actionRequest)
  const [eliminationData, setEliminationData] = useState<EliminationData | null>(null)

  useEffect(() => {
    if (eliminationData) {
      const timer = setTimeout(() => setEliminationData(null), 3500)
      return () => clearTimeout(timer)
    }
  }, [eliminationData])

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
      <GameLayout />
      {actionRequest && <ActionPanel onSubmit={handleActionSubmit} />}
      <PhaseOverlay />
      {eliminationData && (
        <EliminationModal
          playerName={eliminationData.playerName}
          role={eliminationData.role}
          reason={eliminationData.reason}
          onClose={() => setEliminationData(null)}
        />
      )}
    </>
  )
}

// Wrapper for Game Over Screen
function GameOverScreenWrapper() {
  const winner = useGameStore((s) => s.winner)
  return winner ? <GameOverScreen /> : null
}

export default function App() {
  const screen = useGameStore((s) => s.screen)
  usePhaseTheme()

  return (
    <>
      <AnimatePresence mode="wait">
        {screen === 'landing' && <LandingScreen key="landing" />}
        {screen === 'lobby' && <LobbyScreenWrapper key="lobby" />}
        {screen === 'game' && <GameScreenWrapper key="game" />}
        {screen === 'spectate' && <SpectatorScreen key="spectate" />}
        {screen === 'reveal' && <RevealScreen key="reveal" />}
        {screen === 'game_over' && <GameOverScreenWrapper key="game_over" />}
      </AnimatePresence>
      <TxToast />
    </>
  )
}
