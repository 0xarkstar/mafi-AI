"""House AI player implementation."""

from src.agents.llm_client import LLMClient
from src.agents.prompts import (
    build_discussion_prompt,
    build_night_action_prompt,
    build_system_prompt,
    build_vote_prompt,
)
from src.config.constants import PlayerType
from src.models.agent import Personality
from src.players.protocol import TurnContext
from src.utils.logger import get_logger

log = get_logger(__name__)


class HouseAIPlayer:
    """House AI player that wraps existing LLMClient."""

    def __init__(self, name: str, personality: Personality, llm_client: LLMClient):
        """Initialize House AI player.

        Args:
            name: Player name.
            personality: Player personality.
            llm_client: LLM client for AI operations.
        """
        self.name = name
        self.personality = personality
        self.player_type = PlayerType.HOUSE_AI
        self.llm_client = llm_client
        self.wallet_address = None

    async def generate_statement(self, context: TurnContext) -> str:
        """Generate discussion statement using LLM.

        Args:
            context: Current game context.

        Returns:
            Generated statement.
        """
        log.info("house_ai_generating_statement", name=self.name)

        system_prompt = build_system_prompt(
            personality=self.personality,
            role=context.role,
            game_rules="Standard Mafia rules apply.",
        )

        user_prompt = build_discussion_prompt(
            personality=self.personality,
            role=context.role,
            round_events=context.round_history,
            memory=context.memory,
            alive_agents=context.alive_agents,
        )

        statement = await self.llm_client.generate_dialogue(system_prompt, user_prompt)

        log.info(
            "house_ai_statement_generated", name=self.name, length=len(statement)
        )

        return statement

    async def vote(self, context: TurnContext, candidates: list[str]) -> str:
        """Vote using LLM decision making.

        Args:
            context: Current game context.
            candidates: Valid voting targets.

        Returns:
            Chosen candidate name.
        """
        log.info(
            "house_ai_voting",
            name=self.name,
            num_candidates=len(candidates),
        )

        system_prompt = build_system_prompt(
            personality=self.personality,
            role=context.role,
            game_rules="Standard Mafia rules apply.",
        )

        user_prompt = build_vote_prompt(
            personality=self.personality,
            role=context.role,
            discussion_log=context.round_history,
            alive_agents=context.alive_agents,
            memory=context.memory,
        )

        vote = await self.llm_client.make_decision(system_prompt, user_prompt, candidates)

        log.info("house_ai_vote_cast", name=self.name, vote=vote)

        return vote

    async def night_action(self, context: TurnContext, targets: list[str]) -> str:
        """Perform night action using LLM decision making.

        Args:
            context: Current game context.
            targets: Valid action targets.

        Returns:
            Chosen target name.
        """
        log.info(
            "house_ai_night_action",
            name=self.name,
            role=context.role.value,
            num_targets=len(targets),
        )

        system_prompt = build_system_prompt(
            personality=self.personality,
            role=context.role,
            game_rules="Standard Mafia rules apply.",
        )

        user_prompt = build_night_action_prompt(
            role=context.role,
            alive_agents=context.alive_agents,
            known_roles=context.known_roles,
            memory=context.memory,
        )

        target = await self.llm_client.make_decision(system_prompt, user_prompt, targets)

        log.info("house_ai_action_chosen", name=self.name, target=target)

        return target
