"""Betting manager coordinating pools and odds during a game."""

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

from src.agents.llm_client import LLMClient
from src.betting.odds import apply_early_bonus, calculate_implied_odds
from src.betting.oddsmaker import calculate_ai_odds
from src.betting.pool import calculate_payout
from src.config.constants import BetType, DEFAULT_STARTING_CHIPS, HOUSE_EDGE, PlayerType
from src.models.betting import Bet, BettingPool, OddsBoard
from src.models.game import GameState
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.players.protocol import PlayerProtocol

log = get_logger(__name__)


class BettingManager:
    """Manages betting pools and odds during a game."""

    def __init__(self, llm_client: LLMClient, game_id: str):
        """Initialize betting manager.

        Args:
            llm_client: LLM client for AI odds calculation.
            game_id: Game ID for this betting session.
        """
        self.claude = llm_client
        self.game_id = game_id
        self.pools: dict[BetType, BettingPool] = {
            BetType.SIDE_WIN: BettingPool(game_id=game_id, bet_type=BetType.SIDE_WIN),
            BetType.NEXT_ELIMINATION: BettingPool(
                game_id=game_id, bet_type=BetType.NEXT_ELIMINATION
            ),
            BetType.IS_MAFIA: BettingPool(game_id=game_id, bet_type=BetType.IS_MAFIA),
            BetType.IS_AI_OR_HUMAN: BettingPool(game_id=game_id, bet_type=BetType.IS_AI_OR_HUMAN),
        }
        self.spectators: dict[str, Decimal] = {}  # session_id → chips
        self.odds_board: OddsBoard | None = None

    def register_spectator(
        self, session_id: str, chips: int = DEFAULT_STARTING_CHIPS
    ) -> None:
        """Register a spectator with starting chips.

        Args:
            session_id: Unique session ID for spectator.
            chips: Starting chip amount.
        """
        if session_id not in self.spectators:
            self.spectators[session_id] = Decimal(str(chips))
            log.info("spectator_registered", session_id=session_id, chips=chips)

    def place_bet(
        self,
        session_id: str,
        bet_type: str,
        target: str,
        amount: int,
        round_number: int,
    ) -> Bet | None:
        """Place a bet in the pool.

        Args:
            session_id: Spectator session ID.
            bet_type: Type of bet (side_win, next_elimination, is_mafia).
            target: Bet target (e.g., "mafia", "citizens", agent name).
            amount: Bet amount in chips.
            round_number: Current round number.

        Returns:
            Created Bet if successful, None if invalid.
        """
        # Auto-register spectator if not registered
        if session_id not in self.spectators:
            self.register_spectator(session_id)

        # Validate amount
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            log.warning("bet_rejected", reason="invalid_amount", amount=amount)
            return None

        # Check balance
        if self.spectators[session_id] < amount_decimal:
            log.warning(
                "bet_rejected",
                reason="insufficient_chips",
                balance=float(self.spectators[session_id]),
                amount=amount,
            )
            return None

        # Validate bet type
        try:
            bet_type_enum = BetType(bet_type)
        except ValueError:
            log.warning("bet_rejected", reason="invalid_bet_type", bet_type=bet_type)
            return None

        # Create bet
        bet = Bet(
            bet_id=str(uuid4()),
            game_id=self.game_id,
            bettor_id=session_id,
            bet_type=bet_type_enum,
            target=target,
            amount=amount_decimal,
            round_placed=round_number,
        )

        # Apply early bonus
        bet = apply_early_bonus(bet, round_number)

        # Add to pool (immutably)
        pool = self.pools[bet_type_enum]
        new_bets = pool.bets + (bet,)
        new_total = pool.total_amount + bet.amount

        self.pools[bet_type_enum] = pool.model_copy(
            update={"bets": new_bets, "total_amount": new_total}
        )

        # Deduct chips from spectator balance
        self.spectators[session_id] -= bet.amount

        log.info(
            "bet_placed",
            session_id=session_id,
            bet_type=bet_type,
            target=target,
            amount=amount,
            weight=float(bet.weight),
            new_balance=float(self.spectators[session_id]),
        )

        return bet

    async def update_odds(self, game_state: GameState) -> OddsBoard:
        """Update odds board based on game state.

        Args:
            game_state: Current game state.

        Returns:
            Updated OddsBoard.
        """
        # Calculate AI odds
        odds_board = await calculate_ai_odds(game_state, self.claude)

        # Calculate implied odds from betting pools
        side_pool = self.pools[BetType.SIDE_WIN]
        if side_pool.bets:
            implied = calculate_implied_odds(side_pool)
            # Blend AI odds with market odds (70% AI, 30% market)
            if "mafia" in implied and "citizens" in implied:
                mafia_ai = odds_board.mafia_win_prob
                citizen_ai = odds_board.citizen_win_prob

                mafia_market = implied.get("mafia", Decimal("0.5"))
                citizen_market = implied.get("citizens", Decimal("0.5"))

                blended_mafia = (
                    mafia_ai * Decimal("0.7") + mafia_market * Decimal("0.3")
                )
                blended_citizen = (
                    citizen_ai * Decimal("0.7") + citizen_market * Decimal("0.3")
                )

                # Normalize to sum to 1.0
                total = blended_mafia + blended_citizen
                if total > 0:
                    blended_mafia = blended_mafia / total
                    blended_citizen = blended_citizen / total

                odds_board = odds_board.model_copy(
                    update={
                        "mafia_win_prob": blended_mafia,
                        "citizen_win_prob": blended_citizen,
                    }
                )

        self.odds_board = odds_board

        log.info(
            "odds_updated",
            round=game_state.round_number,
            mafia_win=float(odds_board.mafia_win_prob),
            citizen_win=float(odds_board.citizen_win_prob),
        )

        return odds_board

    def settle(self, winner: str) -> dict[str, Decimal]:
        """Settle all bets and distribute payouts.

        Args:
            winner: Winner of the game ("mafia" or "citizens").

        Returns:
            Dict of session_id → total payout amount.
        """
        # Settle side_win pool
        side_pool = self.pools[BetType.SIDE_WIN]
        payouts = calculate_payout(side_pool, winner)

        # Apply payouts to spectator balances
        for session_id, payout in payouts.items():
            if session_id in self.spectators:
                self.spectators[session_id] += payout
            else:
                self.spectators[session_id] = payout

        log.info(
            "bets_settled",
            winner=winner,
            total_payouts=len(payouts),
            total_amount=float(sum(payouts.values())),
        )

        return payouts

    def get_spectator_balance(self, session_id: str) -> Decimal:
        """Get spectator chip balance.

        Args:
            session_id: Spectator session ID.

        Returns:
            Current chip balance.
        """
        if session_id not in self.spectators:
            self.register_spectator(session_id)
        return self.spectators[session_id]

    def settle_identity_bets(self, players: dict[str, "PlayerProtocol"]) -> dict[str, Decimal]:
        """Settle identity bets (IS_AI_OR_HUMAN).

        Bet target format: "PlayerName:ai" or "PlayerName:human"

        Args:
            players: Dict of player name to PlayerProtocol implementation.

        Returns:
            Dict of session_id → total payout amount.
        """
        pool = self.pools[BetType.IS_AI_OR_HUMAN]

        if not pool.bets:
            return {}

        # Map each player to their actual identity
        actual_identities: dict[str, str] = {}
        for player_name, player in players.items():
            if player.player_type in (PlayerType.HOUSE_AI, PlayerType.MOLTBOOK_AGENT):
                actual_identities[player_name] = "ai"
            else:  # AGENT_HUMAN, HUMAN
                actual_identities[player_name] = "human"

        # Separate winning and losing bets
        winning_bets: list[Bet] = []
        total_winning_weight = Decimal("0")

        for bet in pool.bets:
            # Parse bet target: "PlayerName:ai" or "PlayerName:human"
            if ":" not in bet.target:
                log.warning("invalid_identity_bet_target", target=bet.target)
                continue

            player_name, prediction = bet.target.rsplit(":", 1)

            if player_name not in actual_identities:
                log.warning("identity_bet_unknown_player", player=player_name)
                continue

            # Check if prediction matches actual identity
            if prediction == actual_identities[player_name]:
                winning_bets.append(bet)
                total_winning_weight += bet.weight * bet.amount

        # Calculate payouts
        payouts: dict[str, Decimal] = {}

        if winning_bets and total_winning_weight > 0:
            # Net pool after house edge
            net_pool = pool.total_amount * (Decimal("1") - Decimal(str(HOUSE_EDGE)))

            for bet in winning_bets:
                weighted_amount = bet.weight * bet.amount
                payout = (weighted_amount / total_winning_weight) * net_pool

                if bet.bettor_id in payouts:
                    payouts[bet.bettor_id] += payout
                else:
                    payouts[bet.bettor_id] = payout

        # Apply payouts to spectator balances
        for session_id, payout in payouts.items():
            if session_id in self.spectators:
                self.spectators[session_id] += payout
            else:
                self.spectators[session_id] = payout

        log.info(
            "identity_bets_settled",
            total_payouts=len(payouts),
            total_amount=float(sum(payouts.values())),
            num_winning_bets=len(winning_bets),
            num_total_bets=len(pool.bets),
        )

        return payouts
