"""Tests for bet REST endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.bet_routes import router


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    app.state.betting_manager = None
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def mock_bet():
    bet = MagicMock()
    bet.bet_id = "bet-123"
    bet.bet_type.value = "side_win"
    bet.target = "citizens"
    bet.amount = 1.5
    bet.weight = 1.5
    bet.tx_hash = "0xabc"
    return bet


@pytest.fixture
def mock_odds_board():
    board = MagicMock()
    board.mafia_win_prob = 0.4
    board.citizen_win_prob = 0.6
    return board


def test_place_bet_missing_x402_payment(client):
    """Should return error when X402 payment info is missing."""
    resp = client.post(
        "/api/bets",
        json={
            "bet_type": "side_win",
            "target": "citizens",
            "amount_usdc": 1.5,
            "round": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "X402 payment info missing" in data["error"]


def test_place_bet_missing_betting_manager(app, mock_bet):
    """Should return error when betting manager is not enabled."""
    # Set up X402 payment but no betting manager
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class InjectPaymentMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            payment = MagicMock()
            payment.payer_address = "0xpayer"
            payment.tx_hash = "0xhash"
            request.state.x402_payment = payment
            return await call_next(request)

    app.add_middleware(InjectPaymentMiddleware)
    app.state.betting_manager = None

    test_client = TestClient(app)
    resp = test_client.post(
        "/api/bets",
        json={
            "bet_type": "side_win",
            "target": "citizens",
            "amount_usdc": 1.5,
            "round": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Betting not enabled" in data["error"]


def test_place_bet_invalid_bet_returns_error(app, mock_odds_board):
    """Should return error when bet placement returns None (invalid bet)."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class InjectPaymentMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            payment = MagicMock()
            payment.payer_address = "0xpayer"
            payment.tx_hash = "0xhash"
            request.state.x402_payment = payment
            return await call_next(request)

    app.add_middleware(InjectPaymentMiddleware)

    manager = MagicMock()
    manager.place_bet.return_value = None
    manager.odds_board = mock_odds_board
    app.state.betting_manager = manager

    test_client = TestClient(app)
    resp = test_client.post(
        "/api/bets",
        json={
            "bet_type": "side_win",
            "target": "citizens",
            "amount_usdc": 1.5,
            "round": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["error"] == "Invalid bet"


def test_place_bet_success(app, mock_bet, mock_odds_board):
    """Should return bet details on successful placement."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class InjectPaymentMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            payment = MagicMock()
            payment.payer_address = "0xpayer"
            payment.tx_hash = "0xhash"
            request.state.x402_payment = payment
            return await call_next(request)

    app.add_middleware(InjectPaymentMiddleware)

    manager = MagicMock()
    manager.place_bet.return_value = mock_bet
    manager.odds_board = mock_odds_board
    app.state.betting_manager = manager

    test_client = TestClient(app)
    resp = test_client.post(
        "/api/bets",
        json={
            "bet_type": "side_win",
            "target": "citizens",
            "amount_usdc": 1.5,
            "round": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["bet_id"] == "bet-123"
    assert data["bet_type"] == "side_win"
    assert data["target"] == "citizens"
    assert data["tx_hash"] == "0xabc"
