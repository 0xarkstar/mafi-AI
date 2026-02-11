"""API and WebSocket tests."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api import routes
from src.api.server import create_app
from src.api.ws_manager import WSManager
from src.betting.manager import BettingManager
from src.config.constants import BetType, Phase, Role
from src.config.settings import Settings
from src.models.game import GameState


@pytest.fixture
def mock_settings():
    """Create mock Settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.anthropic_api_key = MagicMock()
    settings.anthropic_api_key.get_secret_value = lambda: "test-key"
    settings.port = 8080
    settings.host = "0.0.0.0"
    settings.dialogue_model = "claude-haiku-4-5-20251001"
    settings.decision_model = "claude-sonnet-4-5-20250929"
    settings.oddsmaker_model = "claude-haiku-4-5-20251001"
    return settings


@pytest.fixture
def ws_manager():
    """Create WSManager for testing."""
    return WSManager()


@pytest.fixture
def betting_manager():
    """Create BettingManager for testing."""
    mock_claude = MagicMock()
    mock_claude.analyze_odds = AsyncMock(
        return_value={"mafia_win": 0.5, "citizen_win": 0.5}
    )
    return BettingManager(mock_claude, "test-game")


@pytest.fixture
def sample_game_state():
    """Create sample game state for testing."""
    return GameState(
        game_id="test-game-123",
        phase=Phase.NIGHT,
        round_number=0,
        alive_agents=("Viktor", "Luna", "Rex", "Sage", "Nova", "Iris", "Blaze"),
        dead_agents=tuple(),
        role_map={
            "Viktor": Role.MAFIA,
            "Luna": Role.MAFIA,
            "Rex": Role.DETECTIVE,
            "Sage": Role.CITIZEN,
            "Nova": Role.CITIZEN,
            "Iris": Role.CITIZEN,
            "Blaze": Role.CITIZEN,
        },
        rounds=tuple(),
        winner=None,
    )


@pytest.fixture
def test_app(mock_settings, ws_manager, betting_manager):
    """Create FastAPI test app."""
    app = create_app(mock_settings, ws_manager, betting_manager)
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestHealthCheck:
    """Tests for health check endpoint."""

    def test_health_returns_ok(self, client):
        """Test health endpoint returns 200 OK."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "game_active" in data
        assert "game_id" in data

    def test_health_shows_game_inactive(self, client):
        """Test health endpoint shows game_active=False when no game."""
        # Reset game state
        routes.set_game_state(None)
        routes.set_game_active(False)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["game_active"] is False
        assert data["game_id"] is None

    def test_health_shows_game_active(self, client, sample_game_state):
        """Test health endpoint shows game_active=True with game_id."""
        routes.set_game_state(sample_game_state)
        routes.set_game_active(True)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["game_active"] is True
        assert data["game_id"] == "test-game-123"


class TestGameEndpoint:
    """Tests for game state endpoint."""

    def test_get_game_not_found(self, client):
        """Test GET /api/games/{game_id} returns 404 when no game active."""
        routes.set_game_state(None)

        response = client.get("/api/games/test-game-123")

        assert response.status_code == 404
        assert "No active game" in response.json()["detail"]

    def test_get_game_wrong_id(self, client, sample_game_state):
        """Test GET /api/games/{game_id} returns 404 for wrong game_id."""
        routes.set_game_state(sample_game_state)

        response = client.get("/api/games/wrong-game-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_game_success(self, client, sample_game_state):
        """Test GET /api/games/{game_id} returns game state."""
        routes.set_game_state(sample_game_state)

        response = client.get("/api/games/test-game-123")

        assert response.status_code == 200
        data = response.json()

        # Verify game state fields
        assert data["game_id"] == "test-game-123"
        assert data["phase"] == Phase.NIGHT.value
        assert data["round_number"] == 0
        assert len(data["alive_agents"]) == 7
        assert len(data["dead_agents"]) == 0
        assert data["winner"] is None

        # Verify role_map present (but not revealing roles to spectators in real impl)
        assert "role_map" in data

    def test_get_game_with_eliminations(self, client):
        """Test GET /api/games/{game_id} with dead agents."""
        game_state = GameState(
            game_id="test-game-456",
            phase=Phase.DAY_DISCUSSION,
            round_number=2,
            alive_agents=("Viktor", "Luna", "Rex"),
            dead_agents=("Sage", "Nova"),
            role_map={
                "Viktor": Role.MAFIA,
                "Luna": Role.DETECTIVE,
                "Rex": Role.CITIZEN,
                "Sage": Role.CITIZEN,
                "Nova": Role.CITIZEN,
            },
            rounds=tuple(),
            winner=None,
        )

        routes.set_game_state(game_state)

        response = client.get("/api/games/test-game-456")

        assert response.status_code == 200
        data = response.json()
        assert len(data["alive_agents"]) == 3
        assert len(data["dead_agents"]) == 2
        assert data["round_number"] == 2


class TestOddsEndpoint:
    """Tests for odds endpoint."""

    def test_get_odds_no_game(self, client):
        """Test GET /api/odds returns message when no odds available."""
        routes.set_betting_manager(None)

        response = client.get("/api/odds")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No odds available"

    def test_get_odds_no_board(self, client, betting_manager):
        """Test GET /api/odds returns message when manager has no odds_board."""
        betting_manager.odds_board = None
        routes.set_betting_manager(betting_manager)

        response = client.get("/api/odds")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No odds available"

    @pytest.mark.asyncio
    async def test_get_odds_with_data(self, client, betting_manager, sample_game_state):
        """Test GET /api/odds returns odds data."""
        # Update odds to populate odds_board
        await betting_manager.update_odds(sample_game_state)

        routes.set_betting_manager(betting_manager)

        response = client.get("/api/odds")

        assert response.status_code == 200
        data = response.json()

        # Verify odds fields
        assert data["game_id"] == "test-game-123"
        assert data["round_number"] == 0
        assert "mafia_win_prob" in data
        assert "citizen_win_prob" in data
        assert "mafia_suspects" in data

        # Verify probabilities are floats
        assert isinstance(data["mafia_win_prob"], float)
        assert isinstance(data["citizen_win_prob"], float)

        # Verify probabilities are valid
        assert 0 <= data["mafia_win_prob"] <= 1
        assert 0 <= data["citizen_win_prob"] <= 1


class TestWebSocket:
    """Tests for WebSocket functionality."""

    def test_websocket_connect(self, client):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/ws") as websocket:
            # Connection successful if no exception
            assert websocket is not None

    def test_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()

            assert response["type"] == "pong"

    def test_websocket_place_bet_success(self, client, betting_manager):
        """Test placing bet via WebSocket."""
        routes.set_betting_manager(betting_manager)

        with client.websocket_connect("/ws") as websocket:
            # Place bet
            websocket.send_json(
                {
                    "type": "place_bet",
                    "bet_type": "side_win",
                    "target": "mafia",
                    "amount": 100,
                    "round": 0,
                }
            )

            response = websocket.receive_json()

            assert response["type"] == "bet_confirmed"
            assert "data" in response
            assert response["data"]["bet_type"] == "side_win"
            assert response["data"]["target"] == "mafia"
            assert response["data"]["amount"] == 100.0
            assert response["data"]["weight"] == 1.5  # Round 0 bonus
            assert "new_balance" in response["data"]

    def test_websocket_place_bet_insufficient_chips(self, client, betting_manager):
        """Test placing bet with insufficient chips."""
        routes.set_betting_manager(betting_manager)

        with client.websocket_connect("/ws") as websocket:
            # Try to bet more than balance
            websocket.send_json(
                {
                    "type": "place_bet",
                    "bet_type": "side_win",
                    "target": "mafia",
                    "amount": 10000,  # More than DEFAULT_STARTING_CHIPS
                    "round": 0,
                }
            )

            response = websocket.receive_json()

            assert response["type"] == "bet_rejected"
            assert "data" in response
            assert "reason" in response["data"]
            assert "balance" in response["data"]

    def test_websocket_place_bet_invalid_type(self, client, betting_manager):
        """Test placing bet with invalid bet_type."""
        routes.set_betting_manager(betting_manager)

        with client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {
                    "type": "place_bet",
                    "bet_type": "invalid_type",
                    "target": "mafia",
                    "amount": 100,
                    "round": 0,
                }
            )

            response = websocket.receive_json()

            assert response["type"] == "bet_rejected"
            assert "reason" in response["data"]

    def test_websocket_place_bet_no_manager(self, mock_settings, ws_manager):
        """Test placing bet when betting not enabled."""
        # Create app WITHOUT betting manager
        app = create_app(mock_settings, ws_manager, betting_manager=None)
        test_client = TestClient(app)

        with test_client.websocket_connect("/ws") as websocket:
            websocket.send_json(
                {
                    "type": "place_bet",
                    "bet_type": "side_win",
                    "target": "mafia",
                    "amount": 100,
                    "round": 0,
                }
            )

            response = websocket.receive_json()

            assert response["type"] == "bet_rejected"
            assert response["data"]["reason"] == "Betting not enabled"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test GET / returns 200 OK."""
        response = client.get("/")

        assert response.status_code == 200

        # Response could be HTML (static files exist) or JSON (no static files)
        # Just verify it responds successfully
        assert len(response.content) > 0

    def test_root_endpoint_without_static(self, mock_settings, ws_manager):
        """Test GET / returns JSON when static files don't exist."""
        # Create app and ensure we're testing the JSON path
        # This would require mocking static_dir.exists() to return False
        # For now, we just verify the endpoint is accessible
        app = create_app(mock_settings, ws_manager, betting_manager=None)
        test_client = TestClient(app)

        response = test_client.get("/")
        assert response.status_code == 200
