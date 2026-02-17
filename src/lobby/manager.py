"""Lobby manager for game setup."""

from __future__ import annotations

import time

from src.agents.llm_client import LLMClient
from src.agents.personalities import ALL_PERSONALITIES
from src.config.constants import TOTAL_PLAYERS
from src.models.agent import Personality
from src.players.house_ai import HouseAIPlayer
from src.players.protocol import PlayerProtocol
from src.utils.logger import get_logger

log = get_logger(__name__)


class LobbyManager:
    """Manages player lobby for game setup."""

    def __init__(self, max_players: int = TOTAL_PLAYERS):
        """Initialize lobby manager.

        Args:
            max_players: Maximum number of players allowed.
        """
        self.max_players = max_players
        self.players: dict[str, PlayerProtocol] = {}
        self.player_metadata: dict[str, dict] = {}
        self.first_join_time: float | None = None

    def join(self, player: PlayerProtocol, metadata: dict | None = None) -> bool:
        """Add player to lobby.

        Args:
            player: Player to add.
            metadata: Optional metadata dict (e.g. {"avatar_index": 3}).

        Returns:
            True if added successfully, False if lobby is full.
        """
        if len(self.players) >= self.max_players:
            log.warning("lobby_full", max_players=self.max_players)
            return False

        if self.first_join_time is None:
            self.first_join_time = time.time()

        if player.name in self.players:
            # Allow re-join (e.g. WebSocket reconnect) — replace player instance
            log.info("player_rejoined", name=player.name)
            self.players[player.name] = player
            if metadata:
                self.player_metadata[player.name] = metadata
            return True

        self.players[player.name] = player
        if metadata:
            self.player_metadata[player.name] = metadata
        log.info(
            "player_joined",
            name=player.name,
            player_type=player.player_type.value,
            count=len(self.players),
        )

        return True

    def reset(self) -> None:
        """Clear all players and metadata for next game."""
        self.players.clear()
        self.player_metadata.clear()
        self.first_join_time = None

    def get_lobby_status(self) -> dict:
        """Return structured lobby status with metadata."""
        return {
            "players": [
                {
                    "name": name,
                    "player_type": p.player_type.value,
                    "avatar_index": self.player_metadata.get(name, {}).get("avatar_index"),
                    "wallet_address": getattr(p, "wallet_address", None),
                }
                for name, p in self.players.items()
            ],
            "count": len(self.players),
            "max_players": self.max_players,
            "ready": self.is_ready(),
        }

    def fill_with_house_ai(
        self, llm_client: LLMClient, personalities: tuple[Personality, ...] | None = None
    ) -> None:
        """Fill remaining slots with House AI players.

        Args:
            llm_client: LLM client for AI operations.
            personalities: Optional tuple of personalities to use.
                         If None, uses ALL_PERSONALITIES.
        """
        personalities = personalities or ALL_PERSONALITIES

        remaining_slots = self.max_players - len(self.players)
        log.info("filling_with_house_ai", remaining_slots=remaining_slots)

        # Find unused personalities
        used_names = set(self.players.keys())
        available_personalities = [p for p in personalities if p.name not in used_names]

        # Fill slots
        for i in range(remaining_slots):
            if i >= len(available_personalities):
                log.warning("not_enough_personalities", needed=remaining_slots)
                break

            personality = available_personalities[i]
            player = HouseAIPlayer(
                name=personality.name,
                personality=personality,
                llm_client=llm_client,
            )

            self.players[personality.name] = player
            log.info("house_ai_added", name=personality.name)

    def is_ready(self) -> bool:
        """Check if lobby is ready to start game.

        Returns:
            True if exactly max_players are in lobby.
        """
        ready = len(self.players) == self.max_players
        log.info("lobby_ready_check", count=len(self.players), ready=ready)
        return ready

    def get_players(self) -> dict[str, PlayerProtocol]:
        """Get all players in lobby.

        Returns:
            Dictionary of player name to player instance.
        """
        return self.players.copy()
