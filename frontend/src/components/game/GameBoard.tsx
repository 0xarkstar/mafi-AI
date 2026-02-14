import { useGameStore } from '../../stores/gameStore'
import { PlayerCard } from './PlayerCard'
import { AGENTS } from '../../lib/constants'

export function GameBoard() {
  const players = useGameStore((s) => s.players)

  const playerList = AGENTS.map((agent) => players[agent.name]).filter(
    (player): player is NonNullable<typeof player> => player !== undefined
  )

  // Split into top (4) and bottom (3) rows for desktop
  const topRow = playerList.slice(0, 4)
  const bottomRow = playerList.slice(4, 7)

  return (
    <div className="space-y-4">
      {/* Desktop layout: 4 + 3 */}
      <div className="hidden lg:grid lg:grid-cols-4 gap-3">
        {topRow.map((player) => (
          <PlayerCard key={player.name} player={player} />
        ))}
      </div>
      <div className="hidden lg:grid lg:grid-cols-3 gap-3">
        {bottomRow.map((player) => (
          <PlayerCard key={player.name} player={player} />
        ))}
      </div>

      {/* Mobile layout: 3 + 2 + 2 */}
      <div className="lg:hidden space-y-3">
        <div className="grid grid-cols-3 gap-3">
          {playerList.slice(0, 3).map((player) => (
            <PlayerCard key={player.name} player={player} />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {playerList.slice(3, 5).map((player) => (
            <PlayerCard key={player.name} player={player} />
          ))}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {playerList.slice(5, 7).map((player) => (
            <PlayerCard key={player.name} player={player} />
          ))}
        </div>
      </div>
    </div>
  )
}
