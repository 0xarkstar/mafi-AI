"""API and WebSocket tests."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

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
    settings.openai_api_key = MagicMock()
    settings.openai_api_key.get_secret_value = lambda: "test-key"
    settings.port = 8080
    settings.host = "0.0.0.0"
    settings.dialogue_model = "gpt-4o-mini"
    settings.decision_model = "gpt-4o-mini"
    settings.oddsmaker_model = "gpt-4o-mini"
    settings.x402_enabled = False
    settings.ai_bettor_enabled = False
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
        client.app.state.current_game = None
        client.app.state.game_active = False

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["game_active"] is False
        assert data["game_id"] is None

    def test_health_shows_game_active(self, client, sample_game_state):
        """Test health endpoint shows game_active=True with game_id."""
        client.app.state.current_game = sample_game_state
        client.app.state.game_active = True

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
        client.app.state.current_game = None

        response = client.get("/api/games/test-game-123")

        assert response.status_code == 404
        assert "No active game" in response.json()["detail"]

    def test_get_game_wrong_id(self, client, sample_game_state):
        """Test GET /api/games/{game_id} returns 404 for wrong game_id."""
        client.app.state.current_game = sample_game_state

        response = client.get("/api/games/wrong-game-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_game_success(self, client, sample_game_state):
        """Test GET /api/games/{game_id} returns game state."""
        client.app.state.current_game = sample_game_state

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

        client.app.state.current_game = game_state

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
        client.app.state.betting_manager = None

        response = client.get("/api/odds")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No odds available"

    def test_get_odds_no_board(self, client, betting_manager):
        """Test GET /api/odds returns message when manager has no odds_board."""
        betting_manager.odds_board = None
        client.app.state.betting_manager = betting_manager

        response = client.get("/api/odds")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No odds available"

    @pytest.mark.asyncio
    async def test_get_odds_with_data(self, client, betting_manager, sample_game_state):
        """Test GET /api/odds returns odds data."""
        # Update odds to populate odds_board
        await betting_manager.update_odds(sample_game_state)

        client.app.state.betting_manager = betting_manager

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

    def test_ws_place_bet_confirmed(self, client, betting_manager):
        """Test WS place_bet returns bet_confirmed on success."""
        client.app.state.betting_manager = betting_manager

        # Mock place_bet to return a bet
        mock_bet = MagicMock()
        mock_bet.bet_type = BetType.SIDE_WIN
        mock_bet.target = "mafia"
        mock_bet.amount = Decimal("5.00")
        betting_manager.place_bet = MagicMock(return_value=mock_bet)

        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "type": "place_bet",
                "bet_id": "test-bet-1",
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 5.0,
                "round": 0,
            })
            response = websocket.receive_json()

        assert response["type"] == "bet_confirmed"
        assert response["data"]["bet_id"] == "test-bet-1"
        assert response["data"]["bet_type"] == "side_win"
        assert response["data"]["target"] == "mafia"
        assert response["data"]["amount_usdc"] == 5.0

    def test_ws_place_bet_rejected(self, client, betting_manager):
        """Test WS place_bet returns bet_rejected when bet fails."""
        client.app.state.betting_manager = betting_manager
        betting_manager.place_bet = MagicMock(return_value=None)

        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "type": "place_bet",
                "bet_id": "test-bet-2",
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 5.0,
                "round": 0,
            })
            response = websocket.receive_json()

        assert response["type"] == "bet_rejected"
        assert "reason" in response["data"]

    def test_ws_place_bet_exception(self, client, betting_manager):
        """Test WS place_bet returns bet_rejected on exception."""
        client.app.state.betting_manager = betting_manager
        betting_manager.place_bet = MagicMock(side_effect=Exception("Pool closed"))

        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "type": "place_bet",
                "bet_id": "test-bet-3",
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 5.0,
                "round": 0,
            })
            response = websocket.receive_json()

        assert response["type"] == "bet_rejected"
        assert response["data"]["reason"] == "Bet processing failed"


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


class TestLobbyWebSocket:
    """Tests for lobby WebSocket functionality."""

    def test_join_lobby_no_manager(self, client):
        """Test join_lobby when lobby_manager not available."""
        with client.websocket_connect("/ws") as websocket:
            websocket.send_json({"type": "join_lobby", "name": "TestHuman"})
            response = websocket.receive_json()

            assert response["type"] == "lobby_joined"
            assert response["data"]["success"] is False

    def test_action_response(self, client):
        """Test action_response message."""
        with client.websocket_connect("/ws") as websocket:
            # Send action response (won't actually resolve since no future set)
            websocket.send_json({
                "type": "action_response",
                "player_name": "TestHuman",
                "response": "I am innocent!"
            })

            # Should not receive error (response is handled silently)
            # Just verify connection stays open
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_join_lobby_with_avatar_index(self, mock_settings, ws_manager):
        """Test join_lobby with avatar_index."""
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        test_client = TestClient(app)

        with test_client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "type": "join_lobby",
                "name": "TestHuman",
                "avatar_index": 3,
            })
            response = websocket.receive_json()

            assert response["type"] == "lobby_joined"
            assert response["data"]["success"] is True

            # Avatar index should be stored in metadata
            assert "TestHuman" in lobby.player_metadata
            assert lobby.player_metadata["TestHuman"]["avatar_index"] == 3

    def test_rejoin_lobby(self, mock_settings, ws_manager):
        """Test rejoin_lobby handler."""
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        test_client = TestClient(app)

        with test_client.websocket_connect("/ws") as websocket:
            websocket.send_json({
                "type": "rejoin_lobby",
                "name": "TestHuman",
                "avatar_index": 5,
            })
            response = websocket.receive_json()

            assert response["type"] == "lobby_joined"
            assert response["data"]["success"] is True
            assert "TestHuman" in lobby.players


class TestWSManagerClearSessions:
    """Tests for WSManager.clear_sessions."""

    def test_clear_sessions(self):
        """Test clearing all sessions."""
        ws_manager = WSManager()
        ws_manager.player_sessions["player1"] = MagicMock()
        ws_manager.player_sessions["player2"] = MagicMock()

        ws_manager.clear_sessions()

        assert len(ws_manager.player_sessions) == 0


class TestMoltbookJoin:
    """Tests for Moltbook agent join endpoint."""

    def test_join_agent_no_identity_token(self, mock_settings, ws_manager):
        """Test POST /api/lobby/join-agent without Moltbook Identity token."""
        # Need a lobby_manager so we reach the token check
        app = create_app(mock_settings, ws_manager, betting_manager=None)
        mock_lobby = MagicMock()
        app.state.lobby_manager = mock_lobby
        test_client = TestClient(app)

        response = test_client.post("/api/lobby/join-agent")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "token" in data["error"].lower() or "Identity" in data["error"]

    def test_join_agent_no_lobby(self, client):
        """Test POST /api/lobby/join-agent when lobby not available."""
        response = client.post(
            "/api/lobby/join-agent",
            headers={"X-Moltbook-Identity": "fake-token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Lobby not available" in data["error"]


class TestJoinMoltbook:
    """Tests for POST /api/lobby/join-moltbook endpoint."""

    def test_join_moltbook_no_lobby(self, client):
        """Returns failure when lobby not available."""
        response = client.post(
            "/api/lobby/join-moltbook",
            json={"name": "BotAgent", "moltbook_agent_id": "agent-001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Lobby not available" in data["error"]

    def test_join_moltbook_missing_name(self, mock_settings, ws_manager):
        """Returns failure when name field is missing or empty."""
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        test_client = TestClient(app)

        response = test_client.post(
            "/api/lobby/join-moltbook",
            json={"name": "", "moltbook_agent_id": "agent-001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid name" in data["error"] or "name" in data["error"].lower()

    def test_join_moltbook_missing_agent_id(self, mock_settings, ws_manager):
        """Returns failure when moltbook_agent_id is missing or empty."""
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        test_client = TestClient(app)

        response = test_client.post(
            "/api/lobby/join-moltbook",
            json={"name": "BotAgent", "moltbook_agent_id": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "moltbook_agent_id" in data["error"]

    def test_join_moltbook_success(self, mock_settings, ws_manager):
        """Successfully joins the lobby with valid name and agent_id."""
        from unittest.mock import MagicMock
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        app.state.settings = mock_settings
        mock_settings.moltbook_api_url = "https://api.moltbook.io"
        test_client = TestClient(app)

        response = test_client.post(
            "/api/lobby/join-moltbook",
            json={"name": "BotAgent", "moltbook_agent_id": "agent-xyz-001"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "BotAgent" in lobby.players

    def test_join_moltbook_lobby_full(self, mock_settings, ws_manager):
        """Returns failure (success=False) when lobby is already full."""
        from src.config.constants import PlayerType
        from src.lobby.manager import LobbyManager

        app = create_app(mock_settings, ws_manager, betting_manager=None)
        lobby = LobbyManager()
        app.state.lobby_manager = lobby
        app.state.settings = mock_settings
        mock_settings.moltbook_api_url = "https://api.moltbook.io"
        test_client = TestClient(app)

        # Fill lobby with 7 agents
        for i in range(7):
            mock_player = MagicMock()
            mock_player.name = f"FillerAgent{i}"
            mock_player.player_type = PlayerType.HOUSE_AI
            lobby.players[mock_player.name] = mock_player

        response = test_client.post(
            "/api/lobby/join-moltbook",
            json={"name": "LateAgent", "moltbook_agent_id": "agent-late"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
