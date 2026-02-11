"""Game state repository."""

import json

from src.config.constants import Phase, Role
from src.models.game import GameState, RoundResult
from src.storage.repositories.base import BaseRepository


class GameRepository(BaseRepository[GameState]):
    """Repository for game state persistence."""

    async def save(self, game: GameState) -> None:
        """Save game state to database."""
        # Serialize complex fields to JSON
        role_map_json = json.dumps({k: v.value for k, v in game.role_map.items()})
        state_json = json.dumps({
            "alive_agents": list(game.alive_agents),
            "dead_agents": list(game.dead_agents),
            "rounds": [r.model_dump(mode="json") for r in game.rounds],
        })

        # Upsert game record
        await self._db.execute(
            """
            INSERT INTO games (game_id, phase, round_number, winner, role_map_json, state_json, created_at, ended_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(game_id) DO UPDATE SET
                phase = excluded.phase,
                round_number = excluded.round_number,
                winner = excluded.winner,
                role_map_json = excluded.role_map_json,
                state_json = excluded.state_json,
                ended_at = excluded.ended_at
            """,
            (
                game.game_id,
                game.phase.value,
                game.round_number,
                game.winner,
                role_map_json,
                state_json,
                game.created_at,
                None if game.winner is None else game.created_at,
            ),
        )
        await self._db.commit()

    async def find_by_id(self, game_id: str) -> GameState | None:
        """Find game by ID."""
        row = await self._db.fetchone(
            "SELECT * FROM games WHERE game_id = ?",
            (game_id,),
        )

        if row is None:
            return None

        # Deserialize JSON fields
        role_map = {k: Role(v) for k, v in json.loads(row["role_map_json"]).items()}
        state_data = json.loads(row["state_json"])

        rounds = tuple(
            RoundResult(
                round_number=r["round_number"],
                phase=Phase(r["phase"]),
                eliminated=r.get("eliminated"),
                eliminated_role=Role(r["eliminated_role"]) if r.get("eliminated_role") else None,
                votes=r.get("votes", {}),
                night_kill=r.get("night_kill"),
                detective_target=r.get("detective_target"),
                detective_result=r.get("detective_result"),
            )
            for r in state_data.get("rounds", [])
        )

        return GameState(
            game_id=row["game_id"],
            phase=Phase(row["phase"]),
            round_number=row["round_number"],
            alive_agents=tuple(state_data.get("alive_agents", [])),
            dead_agents=tuple(state_data.get("dead_agents", [])),
            role_map=role_map,
            rounds=rounds,
            winner=row["winner"],
            created_at=row["created_at"],
        )

    async def update_state(self, game: GameState) -> None:
        """Update game state (alias for save)."""
        await self.save(game)
