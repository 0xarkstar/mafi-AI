"""Tests for lobby manager."""

from unittest.mock import MagicMock

import pytest

from src.agents.personalities import ALL_PERSONALITIES
from src.config.constants import TOTAL_PLAYERS, PlayerType
from src.lobby.manager import LobbyManager
from src.models.agent import Personality
from src.players.house_ai import HouseAIPlayer
from src.players.human import HumanPlayer
from src.players.protocol import PlayerProtocol


class MockPlayer:
    """Mock player for testing."""

    def __init__(self, name: str, player_type: PlayerType = PlayerType.HUMAN):
        self.name = name
        self.player_type = player_type


class TestLobbyManager:
    """Tests for LobbyManager."""

    def test_initialization(self):
        """Test lobby manager initialization."""
        lobby = LobbyManager(max_players=7)

        assert lobby.max_players == 7
        assert len(lobby.players) == 0

    def test_default_max_players(self):
        """Test default max_players value."""
        lobby = LobbyManager()

        assert lobby.max_players == TOTAL_PLAYERS

    def test_join_player(self):
        """Test adding a player."""
        lobby = LobbyManager(max_players=3)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)

        result = lobby.join(player1)

        assert result is True
        assert len(lobby.players) == 1
        assert "Alice" in lobby.players

    def test_join_multiple_players(self):
        """Test adding multiple players."""
        lobby = LobbyManager(max_players=3)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        player2 = MockPlayer("Bob", PlayerType.HUMAN)
        player3 = MockPlayer("Charlie", PlayerType.HOUSE_AI)

        assert lobby.join(player1) is True
        assert lobby.join(player2) is True
        assert lobby.join(player3) is True

        assert len(lobby.players) == 3
        assert set(lobby.players.keys()) == {"Alice", "Bob", "Charlie"}

    def test_join_when_full(self):
        """Test joining when lobby is full."""
        lobby = LobbyManager(max_players=2)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        player2 = MockPlayer("Bob", PlayerType.HUMAN)
        player3 = MockPlayer("Charlie", PlayerType.HUMAN)

        assert lobby.join(player1) is True
        assert lobby.join(player2) is True
        assert lobby.join(player3) is False

        assert len(lobby.players) == 2

    def test_join_duplicate_name_allows_rejoin(self):
        """Test joining with duplicate name replaces player (re-join)."""
        lobby = LobbyManager(max_players=3)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        player2 = MockPlayer("Alice", PlayerType.HOUSE_AI)

        assert lobby.join(player1) is True
        assert lobby.join(player2) is True  # re-join allowed

        assert len(lobby.players) == 1
        assert lobby.players["Alice"] is player2  # replaced with new instance

    def test_is_ready_empty(self):
        """Test is_ready when lobby is empty."""
        lobby = LobbyManager(max_players=3)

        assert lobby.is_ready() is False

    def test_is_ready_partial(self):
        """Test is_ready when lobby is partially filled."""
        lobby = LobbyManager(max_players=3)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        lobby.join(player1)

        assert lobby.is_ready() is False

    def test_is_ready_full(self):
        """Test is_ready when lobby is full."""
        lobby = LobbyManager(max_players=2)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        player2 = MockPlayer("Bob", PlayerType.HUMAN)

        lobby.join(player1)
        lobby.join(player2)

        assert lobby.is_ready() is True

    def test_get_players(self):
        """Test get_players returns copy."""
        lobby = LobbyManager(max_players=3)
        player1 = MockPlayer("Alice", PlayerType.HUMAN)
        lobby.join(player1)

        players = lobby.get_players()

        assert len(players) == 1
        assert "Alice" in players

        # Modifying returned dict shouldn't affect lobby
        players["Bob"] = MockPlayer("Bob", PlayerType.HUMAN)
        assert len(lobby.players) == 1

    def test_fill_with_house_ai_empty_lobby(self, mock_llm_client):
        """Test filling empty lobby with House AI."""
        lobby = LobbyManager(max_players=3)

        test_personalities = (
            Personality(
                name="AI1",
                trait="strategist",
                description="Test AI 1",
                speaking_style="formal",
                suspicion_bias=0.5,
            ),
            Personality(
                name="AI2",
                trait="empath",
                description="Test AI 2",
                speaking_style="warm",
                suspicion_bias=0.3,
            ),
            Personality(
                name="AI3",
                trait="bully",
                description="Test AI 3",
                speaking_style="aggressive",
                suspicion_bias=0.8,
            ),
        )

        lobby.fill_with_house_ai(mock_llm_client, test_personalities)

        assert len(lobby.players) == 3
        assert all(isinstance(p, HouseAIPlayer) for p in lobby.players.values())
        assert set(lobby.players.keys()) == {"AI1", "AI2", "AI3"}

    def test_fill_with_house_ai_partial_lobby(self, mock_llm_client):
        """Test filling partially filled lobby."""
        lobby = LobbyManager(max_players=3)
        human = MockPlayer("Human1", PlayerType.HUMAN)
        lobby.join(human)

        test_personalities = (
            Personality(
                name="AI1",
                trait="strategist",
                description="Test AI 1",
                speaking_style="formal",
                suspicion_bias=0.5,
            ),
            Personality(
                name="AI2",
                trait="empath",
                description="Test AI 2",
                speaking_style="warm",
                suspicion_bias=0.3,
            ),
            Personality(
                name="AI3",
                trait="bully",
                description="Test AI 3",
                speaking_style="aggressive",
                suspicion_bias=0.8,
            ),
        )

        lobby.fill_with_house_ai(mock_llm_client, test_personalities)

        assert len(lobby.players) == 3
        assert "Human1" in lobby.players
        # Should add 2 AIs
        ai_count = sum(
            1 for p in lobby.players.values() if isinstance(p, HouseAIPlayer)
        )
        assert ai_count == 2

    def test_fill_with_house_ai_uses_all_personalities(self, mock_llm_client):
        """Test using ALL_PERSONALITIES by default."""
        lobby = LobbyManager(max_players=7)

        lobby.fill_with_house_ai(mock_llm_client)

        assert len(lobby.players) == 7
        assert all(isinstance(p, HouseAIPlayer) for p in lobby.players.values())

        # Should use first 7 personalities from ALL_PERSONALITIES
        expected_names = {p.name for p in ALL_PERSONALITIES[:7]}
        assert set(lobby.players.keys()) == expected_names

    def test_fill_with_house_ai_avoids_duplicates(self, mock_llm_client):
        """Test that fill_with_house_ai avoids duplicate names."""
        lobby = LobbyManager(max_players=3)

        # Add a player with name from personalities
        existing = MockPlayer("AI1", PlayerType.HUMAN)
        lobby.join(existing)

        test_personalities = (
            Personality(
                name="AI1",
                trait="strategist",
                description="Test AI 1",
                speaking_style="formal",
                suspicion_bias=0.5,
            ),
            Personality(
                name="AI2",
                trait="empath",
                description="Test AI 2",
                speaking_style="warm",
                suspicion_bias=0.3,
            ),
            Personality(
                name="AI3",
                trait="bully",
                description="Test AI 3",
                speaking_style="aggressive",
                suspicion_bias=0.8,
            ),
        )

        lobby.fill_with_house_ai(mock_llm_client, test_personalities)

        assert len(lobby.players) == 3
        # Should skip AI1 (already exists) and add AI2 and AI3
        assert set(lobby.players.keys()) == {"AI1", "AI2", "AI3"}

    def test_fill_with_house_ai_not_enough_personalities(self, mock_llm_client):
        """Test filling when not enough personalities available."""
        lobby = LobbyManager(max_players=5)

        test_personalities = (
            Personality(
                name="AI1",
                trait="strategist",
                description="Test AI 1",
                speaking_style="formal",
                suspicion_bias=0.5,
            ),
            Personality(
                name="AI2",
                trait="empath",
                description="Test AI 2",
                speaking_style="warm",
                suspicion_bias=0.3,
            ),
        )

        lobby.fill_with_house_ai(mock_llm_client, test_personalities)

        # Should only add 2 players (not enough personalities for 5)
        assert len(lobby.players) == 2

    def test_full_game_setup_workflow(self, mock_llm_client):
        """Test complete game setup workflow."""
        lobby = LobbyManager(max_players=7)

        # Add 2 human players
        human1 = MockPlayer("Alice", PlayerType.HUMAN)
        human2 = MockPlayer("Bob", PlayerType.AGENT_HUMAN)

        assert lobby.join(human1) is True
        assert lobby.join(human2) is True
        assert lobby.is_ready() is False

        # Fill remaining slots with AI
        lobby.fill_with_house_ai(mock_llm_client)

        assert lobby.is_ready() is True
        assert len(lobby.players) == 7

        # Verify mix of player types
        players = lobby.get_players()
        player_types = {p.player_type for p in players.values()}

        assert PlayerType.HUMAN in player_types
        assert PlayerType.AGENT_HUMAN in player_types
        assert PlayerType.HOUSE_AI in player_types

    def test_player_metadata(self):
        """Test player metadata storage."""
        lobby = LobbyManager(max_players=3)
        player = MockPlayer("Alice", PlayerType.HUMAN)

        lobby.join(player, metadata={"avatar_index": 3})

        assert "Alice" in lobby.player_metadata
        assert lobby.player_metadata["Alice"]["avatar_index"] == 3

    def test_player_metadata_none(self):
        """Test join without metadata."""
        lobby = LobbyManager(max_players=3)
        player = MockPlayer("Alice", PlayerType.HUMAN)

        lobby.join(player)

        assert "Alice" not in lobby.player_metadata

    def test_first_join_time(self):
        """Test first_join_time is set on first join."""
        lobby = LobbyManager(max_players=3)
        player = MockPlayer("Alice", PlayerType.HUMAN)

        assert lobby.first_join_time is None
        lobby.join(player)
        assert lobby.first_join_time is not None

    def test_first_join_time_only_set_once(self):
        """Test first_join_time doesn't change on subsequent joins."""
        lobby = LobbyManager(max_players=3)
        p1 = MockPlayer("Alice", PlayerType.HUMAN)
        p2 = MockPlayer("Bob", PlayerType.HUMAN)

        lobby.join(p1)
        first_time = lobby.first_join_time

        import time
        time.sleep(0.01)
        lobby.join(p2)

        assert lobby.first_join_time == first_time

    def test_reset(self):
        """Test reset clears all state."""
        lobby = LobbyManager(max_players=3)
        p1 = MockPlayer("Alice", PlayerType.HUMAN)
        lobby.join(p1, metadata={"avatar_index": 2})

        assert len(lobby.players) == 1
        assert len(lobby.player_metadata) == 1
        assert lobby.first_join_time is not None

        lobby.reset()

        assert len(lobby.players) == 0
        assert len(lobby.player_metadata) == 0
        assert lobby.first_join_time is None

    def test_get_lobby_status(self):
        """Test get_lobby_status returns structured data."""
        lobby = LobbyManager(max_players=3)
        p1 = MockPlayer("Alice", PlayerType.HUMAN)
        lobby.join(p1, metadata={"avatar_index": 5})

        status = lobby.get_lobby_status()

        assert status["count"] == 1
        assert status["max_players"] == 3
        assert status["ready"] is False
        assert len(status["players"]) == 1
        assert status["players"][0]["name"] == "Alice"
        assert status["players"][0]["player_type"] == "human"
        assert status["players"][0]["avatar_index"] == 5

    def test_get_lobby_status_no_metadata(self):
        """Test get_lobby_status when player has no metadata."""
        lobby = LobbyManager(max_players=3)
        p1 = MockPlayer("Alice", PlayerType.HUMAN)
        lobby.join(p1)

        status = lobby.get_lobby_status()

        assert status["players"][0]["avatar_index"] is None
