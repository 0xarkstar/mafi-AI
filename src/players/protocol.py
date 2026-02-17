"""Player protocol and context definitions."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from src.config.constants import PlayerType, Role
from src.models.agent import Personality
from src.models.game import RoundResult


class TurnContext(BaseModel, frozen=True):
    """Immutable context passed to player methods."""

    alive_agents: tuple[str, ...]
    role: Role
    known_roles: dict[str, Role] = Field(default_factory=dict)
    memory: tuple[str, ...] = ()
    round_number: int = 0
    round_history: tuple[RoundResult, ...] = ()
    personality: Personality | None = None  # For House AI


@runtime_checkable
class PlayerProtocol(Protocol):
    """Protocol that all player types must implement."""

    name: str
    player_type: PlayerType
    wallet_address: str | None

    async def generate_statement(self, context: TurnContext) -> str:
        """Generate a discussion statement during day phase.

        Args:
            context: Current game context.

        Returns:
            Discussion statement as string.
        """
        ...

    async def vote(self, context: TurnContext, candidates: list[str]) -> str:
        """Vote for a player to eliminate during day vote phase.

        Args:
            context: Current game context.
            candidates: List of valid voting targets.

        Returns:
            Name of player to vote for.
        """
        ...

    async def night_action(self, context: TurnContext, targets: list[str]) -> str:
        """Perform night action (mafia kill or detective investigation).

        Args:
            context: Current game context.
            targets: List of valid targets.

        Returns:
            Name of target player.
        """
        ...
