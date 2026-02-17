"""Human player implementations."""

from __future__ import annotations

import asyncio
import random
from typing import Awaitable, Callable

from src.config.constants import PlayerType
from src.players.protocol import TurnContext
from src.utils.logger import get_logger

log = get_logger(__name__)


class HumanPlayer:
    """Human player connected via WebSocket."""

    def __init__(
        self,
        name: str,
        send_to_player: Callable[[dict], Awaitable[None]],
        timeout: int = 60,
        wallet_address: str | None = None,
    ):
        """Initialize human player.

        Args:
            name: Player name.
            send_to_player: Async callback to send messages to player's WebSocket.
            timeout: Response timeout in seconds.
            wallet_address: Optional wallet address for on-chain operations.
        """
        self.name = name
        self.player_type = PlayerType.HUMAN
        self.send_to_player = send_to_player
        self.timeout = timeout
        self.wallet_address = wallet_address
        self._response_future: asyncio.Future[str] | None = None

    def set_response(self, response: str) -> None:
        """Called when player sends response via WebSocket.

        Args:
            response: Player's response (agent name or statement text).
        """
        if self._response_future and not self._response_future.done():
            self._response_future.set_result(response)

    async def _wait_for_response(self, candidates: list[str]) -> str:
        """Wait for player response with timeout.

        Args:
            candidates: Valid choices for random fallback.

        Returns:
            Player response or random choice on timeout.
        """
        # Cancel any existing future to prevent race conditions
        if self._response_future and not self._response_future.done():
            self._response_future.cancel()
        self._response_future = asyncio.Future()

        try:
            response = await asyncio.wait_for(self._response_future, timeout=self.timeout)
            log.info("human_response_received", name=self.name, response=response)
            return response
        except asyncio.TimeoutError:
            fallback = random.choice(candidates)
            log.warning("human_timeout", name=self.name, fallback=fallback)
            return fallback
        finally:
            self._response_future = None

    async def generate_statement(self, context: TurnContext) -> str:
        """Request discussion statement from human.

        Args:
            context: Current game context.

        Returns:
            Human-generated statement or random message on timeout.
        """
        log.info("requesting_human_statement", name=self.name)

        await self.send_to_player(
            {
                "type": "action_request",
                "action_type": "statement",
                "prompt": "It's your turn to speak. Share your thoughts with the group.",
                "options": [],
                "timeout": self.timeout,
                "context": {
                    "role": context.role.value,
                    "alive_agents": list(context.alive_agents),
                    "round_number": context.round_number,
                    "memory": list(context.memory),
                },
            }
        )

        # On timeout, return generic message
        fallback_messages = [
            "I'm thinking about this...",
            "Let me observe for now.",
            "This is interesting.",
        ]

        return await self._wait_for_response(fallback_messages)

    async def vote(self, context: TurnContext, candidates: list[str]) -> str:
        """Request vote from human.

        Args:
            context: Current game context.
            candidates: Valid voting targets.

        Returns:
            Chosen candidate name.
        """
        log.info("requesting_human_vote", name=self.name, num_candidates=len(candidates))

        await self.send_to_player(
            {
                "type": "action_request",
                "action_type": "vote",
                "prompt": "Vote to eliminate a player you suspect is mafia.",
                "options": candidates,
                "timeout": self.timeout,
                "context": {
                    "role": context.role.value,
                    "alive_agents": list(context.alive_agents),
                    "round_number": context.round_number,
                    "memory": list(context.memory),
                },
            }
        )

        return await self._wait_for_response(candidates)

    async def night_action(self, context: TurnContext, targets: list[str]) -> str:
        """Request night action from human.

        Args:
            context: Current game context.
            targets: Valid action targets.

        Returns:
            Chosen target name.
        """
        log.info(
            "requesting_human_night_action",
            name=self.name,
            role=context.role.value,
            num_targets=len(targets),
        )

        await self.send_to_player(
            {
                "type": "action_request",
                "action_type": "night_action",
                "prompt": f"Choose your target for tonight ({context.role.value}).",
                "options": targets,
                "timeout": self.timeout,
                "context": {
                    "role": context.role.value,
                    "alive_agents": list(context.alive_agents),
                    "known_roles": context.known_roles,
                    "memory": list(context.memory),
                },
            }
        )

        return await self._wait_for_response(targets)


class AgentHumanPlayer(HumanPlayer):
    """Human player using agent account (appears as AI)."""

    def __init__(
        self,
        name: str,
        send_to_player: Callable[[dict], Awaitable[None]],
        timeout: int = 60,
        wallet_address: str | None = None,
    ):
        """Initialize agent-human player.

        Args:
            name: Player name.
            send_to_player: Async callback to send messages to player's WebSocket.
            timeout: Response timeout in seconds.
            wallet_address: Optional wallet address for on-chain operations.
        """
        super().__init__(name, send_to_player, timeout, wallet_address)
        self.player_type = PlayerType.AGENT_HUMAN
