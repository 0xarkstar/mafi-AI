"""Base agent abstract class."""

from abc import ABC, abstractmethod

from src.agents.claude_client import ClaudeClient
from src.models.agent import AgentState
from src.models.game import GameState


class BaseAgent(ABC):
    """Abstract base class for AI agents."""

    def __init__(self, state: AgentState, claude_client: ClaudeClient):
        """Initialize agent.

        Args:
            state: Immutable agent state.
            claude_client: Claude API client for AI calls.
        """
        self.state = state
        self.claude = claude_client

    @abstractmethod
    async def generate_statement(self, game_state: GameState, context: str) -> str:
        """Generate a discussion statement.

        Args:
            game_state: Current game state.
            context: Discussion context.

        Returns:
            Agent's statement string.
        """
        ...

    @abstractmethod
    async def vote(self, game_state: GameState, candidates: list[str]) -> str:
        """Vote for elimination.

        Args:
            game_state: Current game state.
            candidates: List of valid vote targets.

        Returns:
            Name of agent to vote for.
        """
        ...

    def update_state(self, **kwargs) -> "BaseAgent":
        """Return new agent with updated state (immutable).

        Args:
            **kwargs: Fields to update in agent state.

        Returns:
            New BaseAgent instance with updated state.
        """
        new_state = self.state.model_copy(update=kwargs)
        return self.__class__(new_state, self.claude)
