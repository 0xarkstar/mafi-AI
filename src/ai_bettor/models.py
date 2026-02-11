"""Frozen Pydantic models for AI Bettor."""

from decimal import Decimal
from pydantic import BaseModel


class GameObservation(BaseModel, frozen=True):
    """Immutable snapshot of game state for betting analysis."""

    game_id: str
    phase: str
    round_number: int
    alive_agents: tuple[str, ...]
    dead_agents: tuple[str, ...]
    recent_events: tuple[str, ...]  # last 10
    current_odds: dict[str, Decimal]


class BetDecision(BaseModel, frozen=True):
    """Immutable betting decision from analyzer."""

    should_bet: bool
    bet_type: str
    target: str
    amount_usdc: Decimal
    confidence: float  # 0.0–1.0
    reasoning: str


class AIBettorState(BaseModel, frozen=True):
    """Immutable state of the AI bettor."""

    balance_usdc: Decimal
    bets_placed: int
    last_bet_time: float | None  # timestamp
    total_wagered: Decimal
    total_won: Decimal
