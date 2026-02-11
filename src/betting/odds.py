"""Dynamic odds calculation from bet distribution."""

from decimal import Decimal

from src.config.constants import EARLY_BET_MULTIPLIERS
from src.models.betting import Bet, BettingPool


def calculate_implied_odds(pool: BettingPool) -> dict[str, Decimal]:
    """Calculate implied odds from bet distribution.

    The implied probability for each target is proportional to the total
    amount bet on that target.

    Args:
        pool: The betting pool to analyze.

    Returns:
        Dict of target → implied probability (0-1). Empty dict if no bets.
    """
    if not pool.bets:
        return {}

    # Aggregate total amount per target
    target_totals: dict[str, Decimal] = {}

    for bet in pool.bets:
        if bet.target in target_totals:
            target_totals[bet.target] += bet.amount
        else:
            target_totals[bet.target] = bet.amount

    # Calculate total pool
    total = sum(target_totals.values())

    if total == 0:
        return {}

    # Calculate implied probability for each target
    implied_odds: dict[str, Decimal] = {}

    for target, amount in target_totals.items():
        implied_odds[target] = amount / total

    return implied_odds


def apply_early_bonus(bet: Bet, round_number: int) -> Bet:
    """Apply early betting bonus weight.

    Round 0: 1.5x weight, Round 1: 1.2x, else 1.0x

    Args:
        bet: The bet to apply bonus to.
        round_number: Current round number when applying bonus.

    Returns:
        New Bet with updated weight (immutable).
    """
    # Determine multiplier based on round
    multiplier = EARLY_BET_MULTIPLIERS.get(round_number, 1.0)

    # Return new bet with updated weight
    return bet.model_copy(update={"weight": Decimal(str(multiplier))})
