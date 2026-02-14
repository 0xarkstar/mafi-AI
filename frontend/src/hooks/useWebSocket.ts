import { useEffect, useRef } from 'react'
import { WebSocketClient } from '../lib/websocket'
import { useGameStore } from '../stores/gameStore'
import { useChatStore } from '../stores/chatStore'
import { useBettingStore } from '../stores/bettingStore'

export function useWebSocket() {
  const wsRef = useRef<WebSocketClient | null>(null)

  const setPhase = useGameStore((s) => s.setPhase)
  const setPlayerAlive = useGameStore((s) => s.setPlayerAlive)
  const setPlayerRole = useGameStore((s) => s.setPlayerRole)
  const setPlayerSpeaking = useGameStore((s) => s.setPlayerSpeaking)
  const setPlayerType = useGameStore((s) => s.setPlayerType)
  const addVote = useGameStore((s) => s.addVote)
  const clearVotes = useGameStore((s) => s.clearVotes)
  const setWinner = useGameStore((s) => s.setWinner)
  const setIsPlayer = useGameStore((s) => s.setIsPlayer)
  const updateLobby = useGameStore((s) => s.updateLobby)
  const setActionRequest = useGameStore((s) => s.setActionRequest)
  const initPlayers = useGameStore((s) => s.initPlayers)

  const addMessage = useChatStore((s) => s.addMessage)
  const addSystemMessage = useChatStore((s) => s.addSystemMessage)

  const setOdds = useBettingStore((s) => s.setOdds)
  const addBet = useBettingStore((s) => s.addBet)
  const updateBetStatus = useBettingStore((s) => s.updateBetStatus)

  useEffect(() => {
    initPlayers()

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
    const ws = new WebSocketClient(wsUrl)

    ws.connect((event) => {
      const { event_type, data } = event

      switch (event_type) {
        case 'phase_change': {
          const phase = data['phase'] as string
          const round = data['round'] as number
          setPhase(phase as any, round)
          addSystemMessage(`Phase changed to ${phase}`)
          if (phase !== 'day_vote') {
            clearVotes()
          }
          break
        }

        case 'agent_message': {
          const agent = data['agent'] as string
          const message = data['message'] as string
          addMessage({ agent, message, type: 'agent' })
          setPlayerSpeaking(agent, true)
          setTimeout(() => setPlayerSpeaking(agent, false), 3000)
          break
        }

        case 'vote_cast': {
          const voter = data['voter'] as string
          const target = data['target'] as string
          addVote(voter, target)
          addSystemMessage(`${voter} voted for ${target}`)
          break
        }

        case 'elimination': {
          const agent = (data['agent'] ?? data['eliminated']) as string
          const role = data['role'] as string
          const reason = data['reason'] as string
          setPlayerAlive(agent, false)
          if (role) setPlayerRole(agent, role as any)
          const reasonText = reason === 'killed_at_night' ? 'killed by the mafia' : 'voted out'
          addSystemMessage(`💀 ${agent} was ${reasonText}${role ? ` (was ${role})` : ''}!`, 'elimination')
          break
        }

        case 'odds_update': {
          const mafiaWinProb = data['mafia_win_prob'] as number
          const citizenWinProb = data['citizen_win_prob'] as number
          const mafiaSuspects = data['mafia_suspects'] as Record<string, number>
          setOdds({
            mafiaWinProb: mafiaWinProb ?? 0.5,
            citizenWinProb: citizenWinProb ?? 0.5,
            mafiaSuspects: mafiaSuspects ?? {},
          })
          break
        }

        case 'game_over': {
          const winner = data['winner'] as string
          setWinner(winner)
          addSystemMessage(`Game Over! ${winner} wins!`, 'game-over')
          break
        }

        case 'bet_placed': {
          const bet = data['bet'] as any
          addBet(bet)
          break
        }

        case 'bet_confirmed': {
          const betId = data['bet_id'] as string
          updateBetStatus(betId, 'won')
          break
        }

        case 'bet_rejected': {
          const betId = data['bet_id'] as string
          updateBetStatus(betId, 'lost')
          break
        }

        case 'lobby_joined': {
          const name = data['name'] as string
          const success = data['success'] as boolean
          if (success) {
            setIsPlayer(true, name)
            addSystemMessage(`You joined as ${name}`)
          } else {
            addSystemMessage('Failed to join lobby')
          }
          break
        }

        case 'lobby_status': {
          const players = data['players'] as string[]
          const count = data['count'] as number
          const ready = data['ready'] as boolean
          updateLobby(players, count, ready)
          break
        }

        case 'game_starting': {
          addSystemMessage('Game starting!')
          break
        }

        case 'action_request': {
          const prompt = data['prompt'] as string
          const actionType = data['action_type'] as string
          const options = data['options'] as string[]
          const timeout = data['timeout'] as number
          setActionRequest({
            prompt,
            actionType: actionType as any,
            options,
            timeout,
          })
          break
        }

        case 'identity_reveal': {
          const playerName = (data['player_name'] ?? data['name']) as string
          const playerType = data['player_type'] as string
          setPlayerType(playerName, playerType as any)
          const typeLabel = playerType === 'human' ? '👤 Human' : '🤖 AI'
          addSystemMessage(`${playerName} is ${typeLabel}`)
          break
        }

        case 'pong':
          // Keepalive response
          break

        default:
          console.warn('Unknown event type:', event_type)
      }
    })

    wsRef.current = ws

    return () => {
      ws.disconnect()
    }
  }, [
    initPlayers,
    setPhase,
    setPlayerAlive,
    setPlayerRole,
    setPlayerSpeaking,
    setPlayerType,
    addVote,
    clearVotes,
    setWinner,
    setIsPlayer,
    updateLobby,
    setActionRequest,
    addMessage,
    addSystemMessage,
    setOdds,
    addBet,
    updateBetStatus,
  ])

  const send = (data: Record<string, unknown>) => {
    wsRef.current?.send(data)
  }

  return { send, connected: wsRef.current?.connected ?? false }
}
