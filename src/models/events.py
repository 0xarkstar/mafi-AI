"""WebSocket event models."""

from typing import Any

from pydantic import BaseModel, Field


class WSEvent(BaseModel, frozen=True):
    """WebSocket event sent to spectators."""

    event_type: str  # phase_change, agent_message, vote_cast, elimination, odds_update, game_over, bet_placed
    data: dict[str, Any] = Field(default_factory=dict)
    game_id: str = ""
    timestamp: str = ""  # ISO format
