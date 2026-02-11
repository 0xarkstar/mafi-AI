"""Pure logic betting strategy without LLM."""

import time
from decimal import Decimal

from src.ai_bettor.models import AIBettorState, GameObservation

# Betting allowed phases
BETTING_PHASES = {"day_discussion", "day_vote"}

# Cooldown between bets (seconds)
BET_COOLDOWN_SECONDS = 30

# Confidence threshold to place bet
MIN_CONFIDENCE = 0.6

# Betting amount range
MIN_BET_AMOUNT = Decimal("1.00")
MAX_BET_AMOUNT = Decimal("10.00")


class BettingStrategy:
    """Pure logic betting strategy."""

    @staticmethod
    def should_bet_now(observation: GameObservation, state: AIBettorState) -> bool:
        """Determine if we should consider betting right now.

        Args:
            observation: Current game state
            state: Current bettor state

        Returns:
            True if timing/conditions allow betting
        """
        # Only bet during specific phases
        if observation.phase not in BETTING_PHASES:
            return False

        # Must have balance
        if state.balance_usdc <= 0:
            return False

        # Enforce cooldown
        if state.last_bet_time is not None:
            time_since_last_bet = time.time() - state.last_bet_time
            if time_since_last_bet < BET_COOLDOWN_SECONDS:
                return False

        return True

    @staticmethod
    def calculate_amount(confidence: float, balance: Decimal) -> Decimal:
        """Calculate bet amount based on confidence.

        Linear scaling: 0.6 → $1, 1.0 → $10

        Args:
            confidence: Confidence level (0.0-1.0)
            balance: Available balance

        Returns:
            Bet amount (0 if confidence too low or insufficient balance)
        """
        # Minimum confidence threshold
        if confidence < MIN_CONFIDENCE:
            return Decimal("0")

        # Linear interpolation between min and max bet
        # confidence 0.6 → 1.0 maps to $1 → $10
        normalized = (confidence - MIN_CONFIDENCE) / (1.0 - MIN_CONFIDENCE)
        amount = MIN_BET_AMOUNT + (MAX_BET_AMOUNT - MIN_BET_AMOUNT) * Decimal(str(normalized))

        # Cap at available balance
        if amount > balance:
            return Decimal("0")

        return amount.quantize(Decimal("0.01"))
