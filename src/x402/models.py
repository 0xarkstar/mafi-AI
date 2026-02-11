"""X402 payment models."""

from decimal import Decimal

from pydantic import BaseModel, Field


class X402BetRequest(BaseModel, frozen=True):
    """Request to place a bet using X402 USDC payment."""

    game_id: str = Field(..., description="Unique game identifier")
    bet_type: str = Field(..., description="Type of bet (BetType enum value)")
    target: str = Field(..., description="Bet target (side, player name, etc.)")
    round_number: int = Field(..., ge=0, description="Round number when bet is placed")
    amount_usdc: Decimal = Field(..., gt=0, description="Bet amount in USDC")


class X402PaymentInfo(BaseModel, frozen=True):
    """Payment information from X402 protocol."""

    payer_address: str = Field(..., description="Ethereum address of payer")
    amount_usdc: Decimal = Field(..., gt=0, description="Amount paid in USDC")
    tx_hash: str = Field(..., description="Transaction hash of payment")
