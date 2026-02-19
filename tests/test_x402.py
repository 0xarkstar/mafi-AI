"""Tests for X402 protocol integration."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from src.x402.models import X402BetRequest, X402PaymentInfo
from src.x402.middleware import X402Middleware
from src.config.settings import Settings


class TestX402Models:
    """Tests for X402 Pydantic models."""

    def test_x402_bet_request_valid(self):
        """Test X402BetRequest with valid input."""
        bet_request = X402BetRequest(
            game_id="game-123",
            bet_type="SIDE_WIN",
            target="citizens",
            round_number=1,
            amount_usdc=Decimal("10.50"),
        )

        assert bet_request.game_id == "game-123"
        assert bet_request.bet_type == "SIDE_WIN"
        assert bet_request.target == "citizens"
        assert bet_request.round_number == 1
        assert bet_request.amount_usdc == Decimal("10.50")

    def test_x402_bet_request_frozen(self):
        """Test X402BetRequest is immutable (frozen)."""
        bet_request = X402BetRequest(
            game_id="game-123",
            bet_type="SIDE_WIN",
            target="citizens",
            round_number=1,
            amount_usdc=Decimal("10.50"),
        )

        with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen models
            bet_request.amount_usdc = Decimal("20.00")

    def test_x402_bet_request_negative_amount_invalid(self):
        """Test X402BetRequest rejects negative amount."""
        with pytest.raises(Exception):  # Pydantic validation error
            X402BetRequest(
                game_id="game-123",
                bet_type="SIDE_WIN",
                target="citizens",
                round_number=1,
                amount_usdc=Decimal("-5.00"),
            )

    def test_x402_bet_request_zero_amount_invalid(self):
        """Test X402BetRequest rejects zero amount."""
        with pytest.raises(Exception):  # Pydantic validation error
            X402BetRequest(
                game_id="game-123",
                bet_type="SIDE_WIN",
                target="citizens",
                round_number=1,
                amount_usdc=Decimal("0"),
            )

    def test_x402_bet_request_negative_round_invalid(self):
        """Test X402BetRequest rejects negative round number."""
        with pytest.raises(Exception):  # Pydantic validation error
            X402BetRequest(
                game_id="game-123",
                bet_type="SIDE_WIN",
                target="citizens",
                round_number=-1,
                amount_usdc=Decimal("10.00"),
            )

    def test_x402_payment_info_valid(self):
        """Test X402PaymentInfo with valid input."""
        payment_info = X402PaymentInfo(
            payer_address="0x1234567890abcdef1234567890abcdef12345678",
            amount_usdc=Decimal("15.00"),
            tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        )

        assert payment_info.payer_address == "0x1234567890abcdef1234567890abcdef12345678"
        assert payment_info.amount_usdc == Decimal("15.00")
        assert payment_info.tx_hash == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_x402_payment_info_frozen(self):
        """Test X402PaymentInfo is immutable (frozen)."""
        payment_info = X402PaymentInfo(
            payer_address="0x1234567890abcdef1234567890abcdef12345678",
            amount_usdc=Decimal("15.00"),
            tx_hash="0xabcdef",
        )

        with pytest.raises(Exception):  # Pydantic raises ValidationError on frozen models
            payment_info.amount_usdc = Decimal("20.00")

    def test_x402_payment_info_negative_amount_invalid(self):
        """Test X402PaymentInfo rejects negative amount."""
        with pytest.raises(Exception):  # Pydantic validation error
            X402PaymentInfo(
                payer_address="0x1234567890abcdef1234567890abcdef12345678",
                amount_usdc=Decimal("-5.00"),
                tx_hash="0xabcdef",
            )

    def test_x402_payment_info_zero_amount_invalid(self):
        """Test X402PaymentInfo rejects zero amount."""
        with pytest.raises(Exception):  # Pydantic validation error
            X402PaymentInfo(
                payer_address="0x1234567890abcdef1234567890abcdef12345678",
                amount_usdc=Decimal("0"),
                tx_hash="0xabcdef",
            )


class TestX402Middleware:
    """Tests for X402 middleware."""

    def test_middleware_disabled_by_default(self):
        """Test middleware is disabled when x402_enabled=False."""
        settings = Settings(x402_enabled=False)
        app = MagicMock()

        middleware = X402Middleware(app, settings)

        assert middleware.enabled is False
        assert middleware.x402_server is None

    @patch("x402.AssetAmount")
    @patch("x402.Money")
    @patch("x402.Network")
    @patch("x402.FacilitatorClient")
    @patch("x402.server.x402ResourceServer")
    def test_middleware_enabled_initializes_server(
        self,
        mock_server_class,
        mock_client_class,
        mock_network,
        mock_money,
        mock_asset_amount,
    ):
        """Test middleware initializes x402 server when enabled."""
        settings = Settings(
            x402_enabled=True,
            x402_facilitator_url="https://facilitator.example.com",
            x402_network="eip155:10143",
            x402_usdc_address="0x1234",
            x402_pay_to="0x5678",
        )
        app = MagicMock()

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_server = MagicMock()
        mock_server_class.return_value = mock_server

        # Mock the x402 classes
        mock_network.return_value = MagicMock()
        mock_money.return_value = MagicMock()
        mock_asset_amount.return_value = MagicMock()

        middleware = X402Middleware(app, settings)

        assert middleware.enabled is True
        mock_client_class.assert_called_once_with(
            facilitator_url="https://facilitator.example.com"
        )
        mock_server_class.assert_called_once_with(facilitator_clients=mock_client)
        mock_server.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_middleware_passthrough_when_disabled(self):
        """Test middleware returns 503 for protected paths when disabled."""
        settings = Settings(x402_enabled=False)
        app = MagicMock()

        middleware = X402Middleware(app, settings, protected_paths=["/api/bets"])

        # Mock request to protected path
        mock_request = MagicMock()
        mock_request.url.path = "/api/bets"
        mock_request.method = "POST"

        mock_call_next = AsyncMock()

        result = await middleware.dispatch(mock_request, mock_call_next)

        # Should return 503 when x402 is disabled for protected paths
        assert result.status_code == 503

    @pytest.mark.asyncio
    async def test_middleware_passthrough_unprotected_path(self):
        """Test middleware passes through requests to unprotected paths."""
        settings = Settings(x402_enabled=True)
        app = MagicMock()

        # Mock x402 initialization to avoid import errors
        with patch("x402.FacilitatorClient"), patch(
            "x402.server.x402ResourceServer"
        ):
            middleware = X402Middleware(app, settings, protected_paths=["/api/bets/x402"])

        # Mock request to unprotected path
        mock_request = MagicMock()
        mock_request.url.path = "/api/games"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_middleware_passthrough_get_request(self):
        """Test middleware passes through GET requests to protected paths."""
        settings = Settings(x402_enabled=True)
        app = MagicMock()

        # Mock x402 initialization
        with patch("x402.FacilitatorClient"), patch(
            "x402.server.x402ResourceServer"
        ):
            middleware = X402Middleware(app, settings, protected_paths=["/api/bets"])

        # Mock GET request to protected path (payment only on POST)
        mock_request = MagicMock()
        mock_request.url.path = "/api/bets/x402"
        mock_request.method = "GET"

        mock_response = MagicMock()
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)


class TestX402Settings:
    """Tests for X402 settings in Settings model."""

    def test_settings_x402_fields_exist(self):
        """Test Settings includes all required X402 fields."""
        settings = Settings()

        assert hasattr(settings, "x402_enabled")
        assert hasattr(settings, "x402_facilitator_url")
        assert hasattr(settings, "x402_network")
        assert hasattr(settings, "x402_usdc_address")
        assert hasattr(settings, "x402_pay_to")

    def test_settings_x402_defaults(self):
        """Test X402 settings have correct defaults."""
        settings = Settings()

        assert settings.x402_enabled is False
        assert settings.x402_facilitator_url == "https://x402-facilitator.molandak.org"
        assert settings.x402_network == "eip155:10143"
        assert settings.x402_usdc_address == "0x534b2f3A21130d7a60830c2Df862319e593943A3"
        assert settings.x402_token_decimals == 6
        assert settings.x402_pay_to == ""

    def test_settings_ai_bettor_fields_exist(self):
        """Test Settings includes AI bettor fields."""
        settings = Settings()

        assert hasattr(settings, "ai_bettor_enabled")
        assert hasattr(settings, "ai_bettor_private_key")
        assert hasattr(settings, "ai_bettor_budget_usdc")

    def test_settings_ai_bettor_defaults(self):
        """Test AI bettor settings have correct defaults."""
        settings = Settings()

        assert settings.ai_bettor_enabled is False
        assert settings.ai_bettor_budget_usdc == 50.0
