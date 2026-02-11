"""Betting models."""

from decimal import Decimal

from pydantic import BaseModel, Field

from src.config.constants import BetType


class Bet(BaseModel, frozen=True):
    """Individual bet placed by a spectator."""

    bet_id: str
    game_id: str
    bettor_id: str  # spectator session id
    bet_type: BetType
    target: str  # "mafia", "citizens", or agent name
    amount: Decimal
    round_placed: int
    weight: Decimal = Decimal("1.0")  # early bet bonus weight


class BettingPool(BaseModel, frozen=True):
    """Collection of bets for a specific bet type."""

    game_id: str
    bet_type: BetType
    bets: tuple[Bet, ...] = ()
    total_amount: Decimal = Decimal("0")


class OddsBoard(BaseModel, frozen=True):
    """Current odds for all bet types."""

    game_id: str
    round_number: int
    mafia_win_prob: Decimal = Decimal("0.5")
    citizen_win_prob: Decimal = Decimal("0.5")
    elimination_odds: dict[str, Decimal] = Field(default_factory=dict)  # name → prob
    mafia_suspects: dict[str, Decimal] = Field(default_factory=dict)  # name → prob
