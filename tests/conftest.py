"""Shared test fixtures for MafiaAI tests."""

import random
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config.constants import Phase, Role
from src.models.agent import AgentState, Personality
from src.models.events import WSEvent
from src.models.game import GameState


@pytest.fixture
def sample_personalities() -> tuple[Personality, ...]:
    """Create sample personalities for testing."""
    return (
        Personality(
            name="TestAgent1",
            trait="strategist",
            description="A test strategist",
            speaking_style="formal",
            suspicion_bias=0.5,
        ),
        Personality(
            name="TestAgent2",
            trait="empath",
            description="A test empath",
            speaking_style="warm",
            suspicion_bias=0.3,
        ),
        Personality(
            name="TestAgent3",
            trait="bully",
            description="A test bully",
            speaking_style="aggressive",
            suspicion_bias=0.8,
        ),
        Personality(
            name="TestAgent4",
            trait="wise",
            description="A test wise elder",
            speaking_style="measured",
            suspicion_bias=0.5,
        ),
        Personality(
            name="TestAgent5",
            trait="observer",
            description="A test observer",
            speaking_style="analytical",
            suspicion_bias=0.6,
        ),
        Personality(
            name="TestAgent6",
            trait="wildcard",
            description="A test wildcard",
            speaking_style="chaotic",
            suspicion_bias=0.5,
        ),
        Personality(
            name="TestAgent7",
            trait="hothead",
            description="A test hothead",
            speaking_style="passionate",
            suspicion_bias=0.9,
        ),
    )


@pytest.fixture
def sample_role_map(sample_personalities: tuple[Personality, ...]) -> dict[str, Role]:
    """Create deterministic role map for testing."""
    return {
        "TestAgent1": Role.MAFIA,
        "TestAgent2": Role.MAFIA,
        "TestAgent3": Role.DETECTIVE,
        "TestAgent4": Role.CITIZEN,
        "TestAgent5": Role.CITIZEN,
        "TestAgent6": Role.CITIZEN,
        "TestAgent7": Role.CITIZEN,
    }


@pytest.fixture
def sample_agents(
    sample_personalities: tuple[Personality, ...],
    sample_role_map: dict[str, Role],
) -> dict[str, AgentState]:
    """Create sample agent states for testing."""
    agents = {}
    for personality in sample_personalities:
        role = sample_role_map[personality.name]

        # Mafia knows each other
        known_roles = {}
        if role == Role.MAFIA:
            known_roles = {
                name: r for name, r in sample_role_map.items() if r == Role.MAFIA
            }

        agents[personality.name] = AgentState(
            name=personality.name,
            personality=personality,
            role=role,
            is_alive=True,
            memory=tuple(),
            known_roles=known_roles,
        )

    return agents


@pytest.fixture
def sample_game_state(
    sample_personalities: tuple[Personality, ...],
    sample_role_map: dict[str, Role],
) -> GameState:
    """Create sample game state with 7 agents, round 0, all alive."""
    agent_names = tuple(p.name for p in sample_personalities)

    return GameState(
        game_id="test-game-123",
        phase=Phase.NIGHT,
        round_number=0,
        alive_agents=agent_names,
        dead_agents=tuple(),
        role_map=sample_role_map,
        rounds=tuple(),
        winner=None,
    )


@pytest.fixture
def event_collector() -> tuple[Callable[[WSEvent], Awaitable[None]], list[WSEvent]]:
    """Create async event collector for capturing WebSocket events.

    Returns:
        Tuple of (callback function, events list).
    """
    events: list[WSEvent] = []

    async def collect_event(event: WSEvent) -> None:
        """Collect event into list."""
        events.append(event)

    return collect_event, events


@pytest.fixture
def mock_claude_client():
    """Create mock ClaudeClient for testing."""
    mock = MagicMock()

    # Default mock responses
    mock.make_decision = AsyncMock(return_value="TestAgent4")
    mock.generate_dialogue = AsyncMock(
        return_value="I think we should investigate TestAgent4."
    )
    mock.analyze_odds = AsyncMock(
        return_value={"mafia_win": 0.5, "citizen_win": 0.5}
    )

    return mock


@pytest.fixture
def seeded_random():
    """Create seeded random generator for deterministic tests."""
    return random.Random(42)
