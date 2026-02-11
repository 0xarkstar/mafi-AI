"""Game state models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.config.constants import Phase, Role


class GameConfig(BaseModel, frozen=True):
    """Game configuration parameters."""

    total_players: int = 7
    mafia_count: int = 2
    detective_count: int = 1
    betting_window_seconds: int = 30
    starting_chips: int = 1000


class RoundResult(BaseModel, frozen=True):
    """Result of a single game round."""

    round_number: int
    phase: Phase
    eliminated: str | None = None  # agent name
    eliminated_role: Role | None = None
    votes: dict[str, str] = Field(default_factory=dict)  # voter → target
    night_kill: str | None = None
    detective_target: str | None = None
    detective_result: bool | None = None  # True = is mafia


class GameState(BaseModel, frozen=True):
    """Immutable game state."""

    game_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase: Phase = Phase.LOBBY
    round_number: int = 0
    alive_agents: tuple[str, ...] = ()
    dead_agents: tuple[str, ...] = ()
    role_map: dict[str, Role] = Field(default_factory=dict)  # agent_name → role
    rounds: tuple[RoundResult, ...] = ()
    winner: str | None = None  # "mafia" or "citizens" or None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
