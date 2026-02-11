"""Moltbook agent player implementation."""

from __future__ import annotations

import random

from src.config.constants import PlayerType
from src.moltbook.client import MoltbookClient
from src.players.protocol import TurnContext
from src.utils.logger import get_logger

log = get_logger(__name__)


class MoltbookAgentPlayer:
    """External AI agent player via Moltbook REST API."""

    def __init__(
        self,
        name: str,
        agent_id: str,
        api_key: str,
        moltbook_client: MoltbookClient,
        timeout: float = 30.0,
    ):
        """Initialize Moltbook agent player.

        Args:
            name: Player name.
            agent_id: Moltbook agent ID.
            api_key: API key for authentication.
            moltbook_client: Moltbook API client.
            timeout: Response timeout in seconds.
        """
        self.name = name
        self.agent_id = agent_id
        self.api_key = api_key
        self.player_type = PlayerType.MOLTBOOK_AGENT
        self.moltbook_client = moltbook_client
        self.timeout = timeout
        self._last_message_id: str | None = None

    async def _request_and_poll(
        self, prompt: str, candidates: list[str]
    ) -> str:
        """Send prompt to agent and poll for response.

        Args:
            prompt: Action prompt to send.
            candidates: Valid choices for fallback.

        Returns:
            Agent response or random choice on timeout/error.
        """
        # Send DM with prompt
        success = await self.moltbook_client.send_dm(
            agent_id=self.agent_id,
            message=prompt,
            api_key=self.api_key,
        )

        if not success:
            log.warning("moltbook_send_failed", name=self.name)
            return random.choice(candidates)

        # Poll for response
        response = await self.moltbook_client.poll_response(
            agent_id=self.agent_id,
            since_id=self._last_message_id,
            api_key=self.api_key,
            timeout=self.timeout,
        )

        if not response:
            log.warning("moltbook_no_response", name=self.name)
            return random.choice(candidates)

        # Parse response to extract valid candidate
        response_lower = response.lower()
        for candidate in candidates:
            if candidate.lower() in response_lower:
                log.info("moltbook_response_parsed", name=self.name, choice=candidate)
                return candidate

        # Fallback to random if no candidate matched
        fallback = random.choice(candidates)
        log.warning(
            "moltbook_parse_failed",
            name=self.name,
            response=response[:100],
            fallback=fallback,
        )
        return fallback

    async def generate_statement(self, context: TurnContext) -> str:
        """Request discussion statement from Moltbook agent.

        Args:
            context: Current game context.

        Returns:
            Generated statement or generic message on error.
        """
        log.info("requesting_moltbook_statement", name=self.name)

        prompt = f"""You are {self.name} playing Mafia.

ROUND: {context.round_number}
ALIVE PLAYERS: {', '.join(context.alive_agents)}
YOUR ROLE: {context.role.value}

RECENT EVENTS:
{chr(10).join(context.memory) if context.memory else "Game just started."}

Make a discussion statement to the group (under 100 words).
"""

        # Send DM with prompt
        success = await self.moltbook_client.send_dm(
            agent_id=self.agent_id,
            message=prompt,
            api_key=self.api_key,
        )

        if not success:
            log.warning("moltbook_send_failed", name=self.name)
            return "I'm carefully observing everyone's behavior."

        # Poll for response
        response = await self.moltbook_client.poll_response(
            agent_id=self.agent_id,
            since_id=self._last_message_id,
            api_key=self.api_key,
            timeout=self.timeout,
        )

        if not response:
            log.warning("moltbook_no_response", name=self.name)
            return "Let me think about this situation."

        # For statement generation, return raw response
        log.info("moltbook_statement_received", name=self.name, length=len(response))
        return response

    async def vote(self, context: TurnContext, candidates: list[str]) -> str:
        """Request vote from Moltbook agent.

        Args:
            context: Current game context.
            candidates: Valid voting targets.

        Returns:
            Chosen candidate name.
        """
        log.info(
            "requesting_moltbook_vote",
            name=self.name,
            num_candidates=len(candidates),
        )

        prompt = f"""You are {self.name} playing Mafia.

ROUND: {context.round_number}
ALIVE PLAYERS: {', '.join(context.alive_agents)}
YOUR ROLE: {context.role.value}

RECENT EVENTS:
{chr(10).join(context.memory) if context.memory else "Game just started."}

Vote for ONE player to eliminate from: {', '.join(candidates)}

Respond with ONLY the player's name.
"""

        return await self._request_and_poll(prompt, candidates)

    async def night_action(self, context: TurnContext, targets: list[str]) -> str:
        """Request night action from Moltbook agent.

        Args:
            context: Current game context.
            targets: Valid action targets.

        Returns:
            Chosen target name.
        """
        log.info(
            "requesting_moltbook_night_action",
            name=self.name,
            role=context.role.value,
            num_targets=len(targets),
        )

        action_name = "kill" if context.role.value == "mafia" else "investigate"

        prompt = f"""You are {self.name} playing Mafia.

ROUND: {context.round_number}
YOUR ROLE: {context.role.value}
ALIVE PLAYERS: {', '.join(context.alive_agents)}

KNOWN ROLES:
{chr(10).join([f"{name}: {role.value}" for name, role in context.known_roles.items()]) if context.known_roles else "None"}

RECENT EVENTS:
{chr(10).join(context.memory) if context.memory else "First night."}

Choose ONE player to {action_name} from: {', '.join(targets)}

Respond with ONLY the player's name.
"""

        return await self._request_and_poll(prompt, targets)
