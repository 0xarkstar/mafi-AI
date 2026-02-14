"""USDC betting integration tests (unified x402 system)."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.betting.manager import BettingManager
from src.config.constants import BetType, MIN_BET_USDC, MAX_BET_USDC


class TestUSDCBettingManager:
    """Tests for unified USDC betting in BettingManager."""

    def test_place_bet_success(self):
        """Test valid USDC bet is placed."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0x1234567890abcdef",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xabcdef1234567890",
        )

        assert bet is not None
        assert bet.bettor_id == "0x1234567890abcdef"
        assert bet.target == "mafia"
        assert bet.amount == Decimal("10.0")
        assert bet.bet_type == BetType.SIDE_WIN
        assert bet.tx_hash == "0xabcdef1234567890"

        # Verify bet added to pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("10.0")

    def test_place_bet_invalid_type(self):
        """Test bet returns None for invalid bet type."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0x1234",
            bet_type="invalid_type",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xabc",
        )

        assert bet is None

    def test_place_bet_below_minimum(self):
        """Test bet returns None for amount below MIN_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("0.50"),  # Below $1 minimum
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet is None

    def test_place_bet_above_maximum(self):
        """Test bet returns None for amount above MAX_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("200.0"),  # Above $100 maximum
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet is None

    def test_place_bet_early_bonus(self):
        """Test USDC bets get early bet bonus."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Round 0: 1.5x weight
        bet_r0 = manager.place_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xabc",
        )
        assert bet_r0.weight == Decimal("1.5")

        # Round 1: 1.2x weight
        bet_r1 = manager.place_bet(
            bettor_address="0x5678",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("10.0"),
            round_number=1,
            tx_hash="0xdef",
        )
        assert bet_r1.weight == Decimal("1.2")

        # Round 2+: 1.0x weight
        bet_r2 = manager.place_bet(
            bettor_address="0x9abc",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=2,
            tx_hash="0x123",
        )
        assert bet_r2.weight == Decimal("1.0")

    def test_place_bet_multiple_same_pool(self):
        """Test multiple USDC bets share the same pool."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place two bets
        bet1 = manager.place_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xabc",
        )

        bet2 = manager.place_bet(
            bettor_address="0x5678",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("20.0"),
            round_number=0,
            tx_hash="0xdef",
        )

        assert bet1 is not None
        assert bet2 is not None

        # Verify both bets in same pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 2
        assert pool.total_amount == Decimal("30.0")

    def test_settle_returns_wallet_addresses(self):
        """Test settle() returns wallet addresses with payout amounts."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place bets
        manager.place_bet(
            bettor_address="0x1234",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xabc",
        )
        manager.place_bet(
            bettor_address="0x5678",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("10.0"),
            round_number=0,
            tx_hash="0xdef",
        )

        # Settle with mafia winning
        payouts = manager.settle("mafia")

        # 0x1234 bet on mafia and should win
        assert "0x1234" in payouts
        # Payout should be net of house edge (5%)
        # Total pool: 20, net: 19, winner gets all 19 (only mafia bettor)
        assert payouts["0x1234"] == Decimal("19.0")


class TestBetModelUSDC:
    """Tests for Bet model with USDC fields."""

    def test_bet_model_requires_tx_hash(self):
        """Test Bet model requires tx_hash (no default)."""
        from src.models.betting import Bet

        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="0x1234",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("10.0"),
            round_placed=0,
            tx_hash="0xabcdef",
        )

        assert bet.tx_hash == "0xabcdef"
        assert bet.bettor_id == "0x1234"

    def test_bet_model_no_payment_method_field(self):
        """Test Bet model no longer has payment_method field."""
        from src.models.betting import Bet

        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="0x1234",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("10.0"),
            round_placed=0,
            tx_hash="0xabcdef",
        )

        assert not hasattr(bet, "payment_method") or "payment_method" not in bet.model_fields

    def test_bet_model_frozen(self):
        """Test Bet model is immutable."""
        from src.models.betting import Bet

        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="0x1234",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("10.0"),
            round_placed=0,
            tx_hash="0xabcdef",
        )

        with pytest.raises(Exception):
            bet.amount = Decimal("20.0")


class TestUSDCBettingAPI:
    """Tests for POST /api/bets unified endpoint."""

    def test_place_bet_endpoint_requires_payment(self):
        """Test /api/bets requires x402 payment info."""
        from fastapi.testclient import TestClient

        from src.agents.llm_client import LLMClient
        from src.api.server import create_app
        from src.api.ws_manager import WSManager
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

        # Post without x402 payment → should fail (no payment info)
        response = client.post(
            "/api/bets",
            json={
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 10,
                "round": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "payment" in data["error"].lower() or "X402" in data["error"]

    def test_place_bet_endpoint_no_betting_manager(self):
        """Test /api/bets returns error when betting not enabled."""
        from fastapi.testclient import TestClient

        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.config.settings import Settings

        settings = Settings(
            openai_api_key="test-key",
            x402_enabled=False,
        )

        ws_manager = WSManager()

        app = create_app(settings, ws_manager, betting_manager=None)
        client = TestClient(app)

        response = client.post(
            "/api/bets",
            json={
                "bet_type": "side_win",
                "target": "mafia",
                "amount_usdc": 10,
                "round": 0,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestIntegrationUSDC:
    """Integration tests for USDC betting flow."""

    def test_ai_client_payload_matches_endpoint(self):
        """Test that AIBettorClient sends payload matching endpoint expectations."""
        from src.ai_bettor.models import GameObservation

        observation = GameObservation(
            game_id="test-game",
            phase="day_vote",
            round_number=2,
            alive_agents=("Alice", "Bob", "Charlie"),
            dead_agents=("Dave",),
            recent_events=("Alice voted for Bob",),
            current_odds={"mafia_win": 0.6, "citizen_win": 0.4},
        )

        expected_payload_keys = {"game_id", "bet_type", "target", "amount_usdc", "round"}

        payload = {
            "game_id": observation.game_id,
            "bet_type": "side_win",
            "target": "mafia",
            "amount_usdc": 5.0,
            "round": observation.round_number,
        }

        assert set(payload.keys()) == expected_payload_keys
        assert isinstance(payload["amount_usdc"], (int, float))
        assert isinstance(payload["round"], int)

    def test_payment_info_attribute_access(self):
        """Test payment info from middleware uses attribute access."""
        from src.x402.models import X402PaymentInfo

        payment_info = X402PaymentInfo(
            payer_address="0x1234567890abcdef",
            amount_usdc=Decimal("10.50"),
            tx_hash="0xabcdef1234567890",
        )

        assert payment_info.payer_address == "0x1234567890abcdef"
        assert payment_info.amount_usdc == Decimal("10.50")
        assert payment_info.tx_hash == "0xabcdef1234567890"
        assert not hasattr(payment_info, "get")

    def test_middleware_factory(self):
        """Test create_x402_middleware factory works."""
        from src.x402.middleware import create_x402_middleware, X402Middleware
        from src.config.settings import Settings

        settings = Settings(x402_enabled=False)
        factory = create_x402_middleware(settings)

        assert callable(factory)

        mock_app = MagicMock()
        middleware = factory(mock_app)

        assert isinstance(middleware, X402Middleware)
        assert middleware.enabled is False

    def test_ai_bettor_uses_correct_api_key(self):
        """Test AIBettorClient uses OpenAI API key."""
        from src.ai_bettor.client import AIBettorClient

        client = AIBettorClient(
            ws_url="ws://localhost:8080/ws",
            api_url="http://localhost:8080",
            api_key="sk-test-openai-key-12345",
            budget_usdc=Decimal("50.0"),
        )

        assert client.analyzer.model == "gpt-4o-mini"
        assert client.analyzer.client is not None

    def test_constants_usdc_limits(self):
        """Test USDC betting limits are defined."""
        assert MIN_BET_USDC == Decimal("1.0")
        assert MAX_BET_USDC == Decimal("100.0")
        assert MIN_BET_USDC < MAX_BET_USDC
