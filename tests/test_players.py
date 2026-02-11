"""Tests for player implementations."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config.constants import PlayerType, Role
from src.models.agent import Personality
from src.players.house_ai import HouseAIPlayer
from src.players.human import AgentHumanPlayer, HumanPlayer
from src.players.moltbook_agent import MoltbookAgentPlayer
from src.players.protocol import TurnContext


@pytest.fixture
def sample_context():
    """Create sample turn context."""
    return TurnContext(
        alive_agents=("Alice", "Bob", "Charlie", "Diana"),
        role=Role.CITIZEN,
        known_roles={},
        memory=("Round 1 started", "Alice spoke"),
        round_number=1,
        round_history=(),
        personality=None,
    )


@pytest.fixture
def sample_personality():
    """Create sample personality."""
    return Personality(
        name="TestAI",
        trait="strategist",
        description="A test AI",
        speaking_style="formal",
        suspicion_bias=0.5,
    )


@pytest.mark.asyncio
class TestHouseAIPlayer:
    """Tests for HouseAIPlayer."""

    async def test_initialization(self, sample_personality, mock_llm_client):
        """Test player initialization."""
        player = HouseAIPlayer(
            name="TestAI",
            personality=sample_personality,
            llm_client=mock_llm_client,
        )

        assert player.name == "TestAI"
        assert player.player_type == PlayerType.HOUSE_AI
        assert player.personality == sample_personality
        assert player.llm_client == mock_llm_client

    async def test_generate_statement(
        self, sample_personality, mock_llm_client, sample_context
    ):
        """Test statement generation."""
        mock_llm_client.generate_dialogue = AsyncMock(
            return_value="I think we should be careful."
        )

        player = HouseAIPlayer(
            name="TestAI",
            personality=sample_personality,
            llm_client=mock_llm_client,
        )

        context = sample_context.model_copy(update={"personality": sample_personality})
        statement = await player.generate_statement(context)

        assert statement == "I think we should be careful."
        mock_llm_client.generate_dialogue.assert_called_once()

    async def test_vote(self, sample_personality, mock_llm_client, sample_context):
        """Test voting."""
        mock_llm_client.make_decision = AsyncMock(return_value="Bob")

        player = HouseAIPlayer(
            name="TestAI",
            personality=sample_personality,
            llm_client=mock_llm_client,
        )

        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        assert vote == "Bob"
        mock_llm_client.make_decision.assert_called_once()

    async def test_night_action(
        self, sample_personality, mock_llm_client, sample_context
    ):
        """Test night action."""
        mock_llm_client.make_decision = AsyncMock(return_value="Charlie")

        player = HouseAIPlayer(
            name="TestAI",
            personality=sample_personality,
            llm_client=mock_llm_client,
        )

        context = sample_context.model_copy(update={"role": Role.MAFIA})
        targets = ["Charlie", "Diana"]
        target = await player.night_action(context, targets)

        assert target == "Charlie"
        mock_llm_client.make_decision.assert_called_once()


@pytest.mark.asyncio
class TestHumanPlayer:
    """Tests for HumanPlayer."""

    async def test_initialization(self):
        """Test player initialization."""
        send_callback = AsyncMock()
        player = HumanPlayer(
            name="Human1",
            send_to_player=send_callback,
            timeout=30,
        )

        assert player.name == "Human1"
        assert player.player_type == PlayerType.HUMAN
        assert player.timeout == 30

    async def test_generate_statement_with_response(self, sample_context):
        """Test statement generation with human response."""
        send_callback = AsyncMock()
        player = HumanPlayer(
            name="Human1",
            send_to_player=send_callback,
            timeout=30,
        )

        # Simulate human response after short delay
        async def simulate_response():
            await asyncio.sleep(0.1)
            player.set_response("This is my statement")

        asyncio.create_task(simulate_response())

        statement = await player.generate_statement(sample_context)

        assert statement == "This is my statement"
        send_callback.assert_called_once()

    async def test_vote_with_timeout(self, sample_context):
        """Test voting with timeout fallback."""
        send_callback = AsyncMock()
        player = HumanPlayer(
            name="Human1",
            send_to_player=send_callback,
            timeout=0.1,  # Very short timeout
        )

        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        # Should return one of the candidates (random fallback)
        assert vote in candidates
        send_callback.assert_called_once()

    async def test_night_action_with_response(self, sample_context):
        """Test night action with human response."""
        send_callback = AsyncMock()
        player = HumanPlayer(
            name="Human1",
            send_to_player=send_callback,
            timeout=30,
        )

        # Simulate human response
        async def simulate_response():
            await asyncio.sleep(0.1)
            player.set_response("Diana")

        asyncio.create_task(simulate_response())

        context = sample_context.model_copy(update={"role": Role.DETECTIVE})
        targets = ["Diana", "Charlie"]
        target = await player.night_action(context, targets)

        assert target == "Diana"
        send_callback.assert_called_once()


@pytest.mark.asyncio
class TestAgentHumanPlayer:
    """Tests for AgentHumanPlayer."""

    async def test_initialization(self):
        """Test player initialization."""
        send_callback = AsyncMock()
        player = AgentHumanPlayer(
            name="AgentHuman1",
            send_to_player=send_callback,
            timeout=30,
        )

        assert player.name == "AgentHuman1"
        assert player.player_type == PlayerType.AGENT_HUMAN

    async def test_inherits_human_behavior(self, sample_context):
        """Test that AgentHumanPlayer behaves like HumanPlayer."""
        send_callback = AsyncMock()
        player = AgentHumanPlayer(
            name="AgentHuman1",
            send_to_player=send_callback,
            timeout=0.1,
        )

        # Should timeout and return fallback
        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        assert vote in candidates


@pytest.mark.asyncio
class TestMoltbookAgentPlayer:
    """Tests for MoltbookAgentPlayer."""

    @pytest.fixture
    def mock_moltbook_client(self):
        """Create mock MoltbookClient."""
        mock = MagicMock()
        mock.send_dm = AsyncMock(return_value=True)
        mock.poll_response = AsyncMock(return_value="Bob")
        return mock

    async def test_initialization(self, mock_moltbook_client):
        """Test player initialization."""
        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        assert player.name == "ExternalAI"
        assert player.agent_id == "agent-123"
        assert player.player_type == PlayerType.MOLTBOOK_AGENT

    async def test_vote_success(self, mock_moltbook_client, sample_context):
        """Test successful vote."""
        mock_moltbook_client.poll_response = AsyncMock(return_value="I vote for Bob")

        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        assert vote == "Bob"
        mock_moltbook_client.send_dm.assert_called_once()
        mock_moltbook_client.poll_response.assert_called_once()

    async def test_vote_send_failure(self, mock_moltbook_client, sample_context):
        """Test vote with send failure."""
        mock_moltbook_client.send_dm = AsyncMock(return_value=False)

        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        # Should fallback to random choice
        assert vote in candidates
        mock_moltbook_client.send_dm.assert_called_once()

    async def test_vote_poll_timeout(self, mock_moltbook_client, sample_context):
        """Test vote with poll timeout."""
        mock_moltbook_client.poll_response = AsyncMock(return_value=None)

        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        candidates = ["Bob", "Charlie"]
        vote = await player.vote(sample_context, candidates)

        # Should fallback to random choice
        assert vote in candidates

    async def test_generate_statement(self, mock_moltbook_client, sample_context):
        """Test statement generation."""
        mock_moltbook_client.poll_response = AsyncMock(
            return_value="I'm observing everyone carefully."
        )

        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        statement = await player.generate_statement(sample_context)

        # Should return the response (not in fallback list)
        assert "observing" in statement.lower()

    async def test_night_action(self, mock_moltbook_client, sample_context):
        """Test night action."""
        mock_moltbook_client.poll_response = AsyncMock(
            return_value="I choose Diana"
        )

        player = MoltbookAgentPlayer(
            name="ExternalAI",
            agent_id="agent-123",
            api_key="test-key",
            moltbook_client=mock_moltbook_client,
            timeout=30.0,
        )

        context = sample_context.model_copy(update={"role": Role.MAFIA})
        targets = ["Diana", "Charlie"]
        target = await player.night_action(context, targets)

        assert target == "Diana"


class TestTurnContext:
    """Tests for TurnContext."""

    def test_immutability(self):
        """Test that TurnContext is frozen."""
        context = TurnContext(
            alive_agents=("Alice", "Bob"),
            role=Role.CITIZEN,
        )

        with pytest.raises(Exception):
            context.alive_agents = ("Charlie",)

    def test_default_values(self):
        """Test default field values."""
        context = TurnContext(
            alive_agents=("Alice", "Bob"),
            role=Role.CITIZEN,
        )

        assert context.known_roles == {}
        assert context.memory == ()
        assert context.round_number == 0
        assert context.round_history == ()
        assert context.personality is None

    def test_with_personality(self, sample_personality):
        """Test context with personality."""
        context = TurnContext(
            alive_agents=("Alice", "Bob"),
            role=Role.CITIZEN,
            personality=sample_personality,
        )

        assert context.personality == sample_personality
