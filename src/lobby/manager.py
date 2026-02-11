"""Lobby manager for game setup."""

from __future__ import annotations

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

    def join(self, player: PlayerProtocol) -> bool:
        """Add player to lobby.

        Args:
            player: Player to add.

        Returns:
            True if added successfully, False if lobby is full.
        """
        if len(self.players) >= self.max_players:
            log.warning("lobby_full", max_players=self.max_players)
            return False

        if player.name in self.players:
            log.warning("player_already_joined", name=player.name)
            return False

        self.players[player.name] = player
        log.info(
            "player_joined",
            name=player.name,
            player_type=player.player_type.value,
            count=len(self.players),
        )

        return True

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
