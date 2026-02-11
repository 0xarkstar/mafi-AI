"""Pari-mutuel betting pool with house edge."""

from decimal import Decimal

from src.config.constants import HOUSE_EDGE
from src.models.betting import Bet, BettingPool


def calculate_payout(pool: BettingPool, winning_target: str) -> dict[str, Decimal]:
    """Calculate payouts for a resolved betting pool.

    Pari-mutuel: all bets pooled, 5% house edge deducted,
    remaining distributed proportionally to winning bets (weighted by early bonus).

    Args:
        pool: The betting pool to resolve.
        winning_target: The target that won (e.g., "mafia", "citizens", agent name).

    Returns:
        Dict of bettor_id → payout amount. Empty dict if no winning bets.
    """
    # Calculate total pool
    total_pool = sum(bet.amount for bet in pool.bets)

    if total_pool == 0:
        return {}

    # Deduct house edge
    net_pool = total_pool * Decimal(str(1 - HOUSE_EDGE))

    # Filter winning bets
    winning_bets = [bet for bet in pool.bets if bet.target == winning_target]

    if not winning_bets:
        # House takes all if no winners
        return {}

    # Calculate total weighted winning amount
    total_weighted_winning = sum(bet.amount * bet.weight for bet in winning_bets)

    if total_weighted_winning == 0:
        return {}

    # Distribute proportionally by weighted amount
    payouts: dict[str, Decimal] = {}

    for bet in winning_bets:
        weighted_amount = bet.amount * bet.weight
        payout = (weighted_amount / total_weighted_winning) * net_pool

        # Aggregate payouts per bettor (in case same bettor has multiple bets)
        if bet.bettor_id in payouts:
            payouts[bet.bettor_id] += payout
        else:
            payouts[bet.bettor_id] = payout

    return payouts
