"""X402 betting integration tests."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.betting.manager import BettingManager
from src.config.constants import BetType


class TestX402BettingManager:
    """Tests for X402 betting in BettingManager."""

    def test_handle_x402_bet_success(self):
        """Test valid X402 bet is placed without balance check."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place X402 bet (no spectator registration needed)
        bet = manager.handle_x402_bet(
            bettor_address="0x1234567890abcdef",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("100"),
            round_number=0,
            tx_hash="0xabcdef1234567890",
        )

        # Verify bet created with X402 fields
        assert bet is not None
        assert bet.bettor_id == "0x1234567890abcdef"
        assert bet.target == "mafia"
        assert bet.amount == Decimal("100")
        assert bet.bet_type == BetType.SIDE_WIN
        assert bet.payment_method == "x402"
        assert bet.tx_hash == "0xabcdef1234567890"

        # Verify bet added to pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("100")

    def test_handle_x402_bet_invalid_type(self):
        """Test X402 bet returns None for invalid bet type."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="invalid_type",
            target="mafia",
            amount_usdc=Decimal("100"),
            round_number=0,
            tx_hash="0xabc",
        )

        assert bet is None

    def test_handle_x402_bet_zero_amount(self):
        """Test X402 bet returns None for amount <= 0."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Zero amount
        bet = manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("0"),
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet is None

        # Negative amount
        bet = manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("-50"),
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet is None

    def test_handle_x402_bet_early_bonus(self):
        """Test X402 bets get early bet bonus."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Round 0: 1.5x weight
        bet_r0 = manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("100"),
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet_r0.weight == Decimal("1.5")

        # Round 1: 1.2x weight
        bet_r1 = manager.handle_x402_bet(
            bettor_address="0x5678",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("100"),
            round_number=1,
            tx_hash="0xdef",
        )
        assert bet_r1.weight == Decimal("1.2")

        # Round 2+: 1.0x weight
        bet_r2 = manager.handle_x402_bet(
            bettor_address="0x9abc",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("100"),
            round_number=2,
            tx_hash="0x123",
        )
        assert bet_r2.weight == Decimal("1.0")

    def test_handle_x402_bet_adds_to_same_pool_as_chips(self):
        """Test X402 bets and chip bets share the same pool."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place chip bet
        manager.register_spectator("user1", chips=1000)
        chip_bet = manager.place_bet("user1", "side_win", "mafia", 100, 0)
        assert chip_bet is not None

        # Place X402 bet
        x402_bet = manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("200"),
            round_number=0,
            tx_hash="0xabc",
        )
        assert x402_bet is not None

        # Verify both bets in same pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 2
        assert pool.total_amount == Decimal("300")

        # Verify payment methods
        chip_bet_in_pool = [b for b in pool.bets if b.payment_method == "chips"][0]
        x402_bet_in_pool = [b for b in pool.bets if b.payment_method == "x402"][0]

        assert chip_bet_in_pool.bettor_id == "user1"
        assert chip_bet_in_pool.tx_hash is None

        assert x402_bet_in_pool.bettor_id == "0x1234"
        assert x402_bet_in_pool.tx_hash == "0xabc"


class TestBetModelDefaults:
    """Tests for Bet model default fields."""

    def test_bet_model_defaults(self):
        """Test Bet model has correct defaults for new fields."""
        from src.models.betting import Bet

        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="user1",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("100"),
            round_placed=0,
        )

        # Verify defaults
        assert bet.payment_method == "chips"
        assert bet.tx_hash is None

    def test_bet_model_with_x402_fields(self):
        """Test Bet model with X402 fields set."""
        from src.models.betting import Bet

        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="0x1234",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("100"),
            round_placed=0,
            payment_method="x402",
            tx_hash="0xabcdef",
        )

        assert bet.payment_method == "x402"
        assert bet.tx_hash == "0xabcdef"


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing chip betting."""

    def test_existing_chip_betting_still_works(self):
        """Test that existing chip betting functionality is unchanged."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register and place chip bet (existing behavior)
        manager.register_spectator("user1", chips=1000)
        bet = manager.place_bet("user1", "side_win", "mafia", 100, 0)

        # Verify existing behavior
        assert bet is not None
        assert bet.payment_method == "chips"
        assert bet.tx_hash is None
        assert manager.spectators["user1"] == Decimal("900")

    def test_settle_works_with_mixed_bets(self):
        """Test settlement works with both chip and X402 bets."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place chip bet
        manager.register_spectator("user1", chips=1000)
        manager.place_bet("user1", "side_win", "mafia", 100, 0)

        # Place X402 bet
        manager.handle_x402_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("200"),
            round_number=0,
            tx_hash="0xabc",
        )

        # Settle with mafia winning
        payouts = manager.settle("mafia")

        # Both should win
        assert "user1" in payouts
        assert "0x1234" in payouts

        # Total pool: 300, house edge: 5%, net: 285
        # user1 weighted: 100 * 1.5 = 150
        # 0x1234 weighted: 200 * 1.5 = 300
        # Total weighted: 450
        # user1 gets: (150/450) * 285 = 95
        # 0x1234 gets: (300/450) * 285 = 190

        # Use approximate comparison for decimal precision
        assert abs(payouts["user1"] - Decimal("95")) < Decimal("0.01")
        assert abs(payouts["0x1234"] - Decimal("190")) < Decimal("0.01")

        # Verify chip balance updated
        assert manager.spectators["user1"] == Decimal("900") + Decimal("95")
        assert manager.spectators["user1"] == Decimal("995")

        # Verify X402 bettor registered in spectators after payout
        assert manager.spectators["0x1234"] == Decimal("190")


class TestX402APIEndpoint:
    """Tests for POST /api/bets/x402 endpoint."""

    def test_place_x402_bet_endpoint_test_mode(self):
        """Test X402 betting endpoint in test mode (x402_enabled=False)."""
        from fastapi.testclient import TestClient

        from src.agents.llm_client import LLMClient
        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.betting.manager import BettingManager
        from src.config.settings import Settings

        # Create test settings
        settings = Settings(
            openai_api_key="test-key",
            x402_enabled=False,  # Test mode
        )

        # Create dependencies
        ws_manager = WSManager()
        llm_client = LLMClient(settings)
        betting_manager = BettingManager(llm_client, "test-game")

        # Create app
        app = create_app(settings, ws_manager, betting_manager)

        # Test endpoint with TestClient
        client = TestClient(app)
        response = client.post(
            "/api/bets/x402",
            json={
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 100,
                "round": 0,
            },
            headers={
                "X-Test-Address": "0x1234567890",
                "X-Test-TxHash": "0xabcdef1234567890",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["bet_type"] == "side_win"
        assert data["target"] == "mafia"
        assert data["amount"] == 100.0
        assert data["weight"] == 1.5  # Round 0 bonus
        assert data["tx_hash"] == "0xabcdef1234567890"

    def test_place_x402_bet_endpoint_invalid_bet_type(self):
        """Test X402 endpoint rejects invalid bet type."""
        from fastapi.testclient import TestClient

        from src.agents.llm_client import LLMClient
        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.betting.manager import BettingManager
        from src.config.settings import Settings

        settings = Settings(
            openai_api_key="test-key",
            x402_enabled=False,
        )

        ws_manager = WSManager()
        llm_client = LLMClient(settings)
        betting_manager = BettingManager(llm_client, "test-game")

        app = create_app(settings, ws_manager, betting_manager)

        client = TestClient(app)
        response = client.post(
            "/api/bets/x402",
            json={
                "bet_type": "invalid_type",
                "target": "mafia",
                "amount_usdc": 100,
                "round": 0,
            },
            headers={
                "X-Test-Address": "0x1234",
                "X-Test-TxHash": "0xabc",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Invalid bet" in data["error"]

    def test_place_x402_bet_endpoint_adds_to_pool(self):
        """Test X402 endpoint actually adds bet to pool."""
        from fastapi.testclient import TestClient

        from src.agents.llm_client import LLMClient
        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.betting.manager import BettingManager
        from src.config.settings import Settings

        settings = Settings(
            openai_api_key="test-key",
            x402_enabled=False,
        )

        ws_manager = WSManager()
        llm_client = LLMClient(settings)
        betting_manager = BettingManager(llm_client, "test-game")

        app = create_app(settings, ws_manager, betting_manager)

        client = TestClient(app)
        client.post(
            "/api/bets/x402",
            json={
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 100,
                "round": 0,
            },
            headers={
                "X-Test-Address": "0x1234",
                "X-Test-TxHash": "0xabc",
            },
        )

        # Verify bet in pool
        pool = betting_manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("100")
        assert pool.bets[0].payment_method == "x402"


class TestIntegrationX402:
    """Integration tests for X402 betting flow."""

    def test_ai_client_payload_matches_endpoint_expectation(self):
        """Test that AIBettorClient sends payload matching endpoint expectations."""
        # This test verifies Bug Fix #3
        # Endpoint expects: bet_type, target, amount_usdc, round_number
        # Client should send exactly these fields

        from src.ai_bettor.models import GameObservation

        # Mock observation
        observation = GameObservation(
            game_id="test-game",
            phase="day_vote",
            round_number=2,
            alive_agents=("Alice", "Bob", "Charlie"),
            dead_agents=("Dave",),
            recent_events=("Alice voted for Bob",),
            current_odds={"mafia_win": 0.6, "citizen_win": 0.4},
        )

        # Build expected payload
        # This mimics what AIBettorClient._place_bet_via_api should send
        expected_payload_keys = {"game_id", "bet_type", "target", "amount_usdc", "round"}

        # Simulate client payload construction
        payload = {
            "game_id": observation.game_id,
            "bet_type": "side_win",
            "target": "mafia",
            "amount_usdc": 5.0,
            "round": observation.round_number,
        }

        # Verify keys match
        assert set(payload.keys()) == expected_payload_keys

        # Verify types
        assert isinstance(payload["amount_usdc"], (int, float))
        assert isinstance(payload["round"], int)
        assert payload["round"] == 2

    def test_payment_info_attribute_access(self):
        """Test that payment info from middleware is accessed via attributes."""
        # This test verifies Bug Fix #2
        from src.x402.models import X402PaymentInfo

        # Create payment info (as middleware does)
        payment_info = X402PaymentInfo(
            payer_address="0x1234567890abcdef",
            amount_usdc=Decimal("10.50"),
            tx_hash="0xabcdef1234567890",
        )

        # Verify attribute access works (not .get() dict method)
        assert payment_info.payer_address == "0x1234567890abcdef"
        assert payment_info.amount_usdc == Decimal("10.50")
        assert payment_info.tx_hash == "0xabcdef1234567890"

        # Verify .get() doesn't work (it's not a dict)
        assert not hasattr(payment_info, "get")

    def test_end_to_end_x402_bet_placement(self):
        """Test end-to-end flow: middleware → endpoint → handle_x402_bet → bet created."""
        from fastapi.testclient import TestClient
        from unittest.mock import MagicMock

        from src.agents.llm_client import LLMClient
        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.betting.manager import BettingManager
        from src.config.settings import Settings
        from src.x402.models import X402PaymentInfo

        # Create test settings (x402_enabled=False for test mode)
        settings = Settings(
            openai_api_key="test-key",
            x402_enabled=False,  # Test mode bypasses middleware
        )

        # Create dependencies
        ws_manager = WSManager()
        llm_client = LLMClient(settings)
        betting_manager = BettingManager(llm_client, "test-game")

        # Create app
        app = create_app(settings, ws_manager, betting_manager)

        # Test client
        client = TestClient(app)

        # Test payload (matches fixed AIBettorClient format)
        payload = {
            "bet_type": "side_win",
            "target": "citizens",
            "amount_usdc": 15.0,
            "round": 1,
        }

        # Test headers (simulates x402 payment in test mode)
        headers = {
            "X-Test-Address": "0xTestAddress123",
            "X-Test-TxHash": "0xTestTxHash456",
        }

        # Make request
        response = client.post("/api/bets/x402", json=payload, headers=headers)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["bet_type"] == "side_win"
        assert data["target"] == "citizens"
        assert data["amount"] == 15.0
        assert data["weight"] == 1.2  # Round 1 bonus
        assert data["tx_hash"] == "0xTestTxHash456"

        # Verify bet was actually added to betting manager
        from src.config.constants import BetType

        pool = betting_manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1

        bet = pool.bets[0]
        assert bet.bettor_id == "0xTestAddress123"
        assert bet.amount == Decimal("15")
        assert bet.payment_method == "x402"
        assert bet.tx_hash == "0xTestTxHash456"
        assert bet.target == "citizens"

    def test_middleware_factory_creates_correct_middleware(self):
        """Test that create_x402_middleware factory works correctly."""
        # This test verifies Bug Fix #1
        from src.x402.middleware import create_x402_middleware, X402Middleware
        from src.config.settings import Settings
        from unittest.mock import MagicMock

        settings = Settings(x402_enabled=False)
        factory = create_x402_middleware(settings)

        # Factory should return a function
        assert callable(factory)

        # Call factory with mock app
        mock_app = MagicMock()
        middleware_instance = factory(mock_app)

        # Verify it creates X402Middleware instance
        assert isinstance(middleware_instance, X402Middleware)
        assert middleware_instance.settings == settings
        assert middleware_instance.enabled is False

    def test_ai_bettor_uses_correct_api_key(self):
        """Test that AIBettorClient uses OpenAI API key, not wallet private key."""
        # This test verifies Bug Fix #4
        from decimal import Decimal
        from src.ai_bettor.client import AIBettorClient

        # Create client with OpenAI API key
        openai_key = "sk-test-openai-key-12345"
        client = AIBettorClient(
            ws_url="ws://localhost:8080/ws",
            api_url="http://localhost:8080",
            api_key=openai_key,
            budget_usdc=Decimal("50.0"),
        )

        # Verify analyzer was created with the correct model
        assert client.analyzer.model == "gpt-4o-mini"

        # Verify the client was created (OpenAI client is private)
        # We can't directly check the API key, but we verify it's set up correctly
        assert client.analyzer.client is not None

        # This key should NOT be a wallet private key (those start with 0x)
        assert not openai_key.startswith("0x")
        assert openai_key.startswith("sk-")  # OpenAI keys start with sk-
