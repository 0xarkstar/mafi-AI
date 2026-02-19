"""Betting REST API routes."""

from decimal import Decimal as D

from fastapi import APIRouter, Request

from src.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


@router.post("/api/bets")
async def place_bet(request: Request):
    """Place a bet via X402 payment protocol (unified endpoint).

    All bets require X402 USDC payment.
    Any X402-compatible client (Moltbook agents, spectator agents,
    AI Bettor) can call this endpoint.
    """
    try:
        body = await request.json()
        bet_type = body.get("bet_type")
        target = body.get("target")
        amount_usdc = body.get("amount_usdc", 0)
        round_number = body.get("round", 0)

        payment_info = getattr(request.state, "x402_payment", None)
        if not payment_info:
            return {"success": False, "error": "X402 payment info missing"}
        bettor_address = payment_info.payer_address
        tx_hash = payment_info.tx_hash

        betting_manager = request.app.state.betting_manager
        if not betting_manager:
            return {"success": False, "error": "Betting not enabled"}

        bet = betting_manager.place_bet(
            bettor_address=bettor_address,
            bet_type=bet_type,
            target=target,
            amount_usdc=D(str(amount_usdc)),
            round_number=round_number,
            tx_hash=tx_hash,
        )

        if not bet:
            return {"success": False, "error": "Invalid bet"}

        odds_board = betting_manager.odds_board
        return {
            "success": True,
            "bet_id": bet.bet_id,
            "bet_type": bet.bet_type.value,
            "target": bet.target,
            "amount": float(bet.amount),
            "weight": float(bet.weight),
            "tx_hash": bet.tx_hash,
            "odds": {
                "mafia_win": float(odds_board.mafia_win_prob) if odds_board else 0.5,
                "citizen_win": float(odds_board.citizen_win_prob) if odds_board else 0.5,
            }
            if odds_board
            else {},
        }

    except ValueError as exc:
        log.warning("bet_validation_error", error=str(exc))
        return {"success": False, "error": f"Invalid bet: {exc}"}
    except Exception as exc:
        log.error("bet_placement_error", error=str(exc))
        return {"success": False, "error": "Internal server error"}
