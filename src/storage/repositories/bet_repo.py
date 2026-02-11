"""Bet repository."""

from decimal import Decimal

from src.config.constants import BetType
from src.models.betting import Bet
from src.storage.repositories.base import BaseRepository


class BetRepository(BaseRepository[Bet]):
    """Repository for bet persistence."""

    async def save(self, bet: Bet) -> None:
        """Save a bet to database."""
        await self._db.execute(
            """
            INSERT INTO bets (bet_id, game_id, bettor_id, bet_type, target, amount, round_placed, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bet.bet_id,
                bet.game_id,
                bet.bettor_id,
                bet.bet_type.value,
                bet.target,
                float(bet.amount),
                bet.round_placed,
                float(bet.weight),
            ),
        )
        await self._db.commit()

    async def find_by_id(self, bet_id: str) -> Bet | None:
        """Find bet by ID."""
        row = await self._db.fetchone(
            "SELECT * FROM bets WHERE bet_id = ?",
            (bet_id,),
        )

        if row is None:
            return None

        return Bet(
            bet_id=row["bet_id"],
            game_id=row["game_id"],
            bettor_id=row["bettor_id"],
            bet_type=BetType(row["bet_type"]),
            target=row["target"],
            amount=Decimal(str(row["amount"])),
            round_placed=row["round_placed"],
            weight=Decimal(str(row["weight"])),
        )

    async def find_by_game(self, game_id: str) -> list[Bet]:
        """Find all bets for a game."""
        rows = await self._db.fetchall(
            "SELECT * FROM bets WHERE game_id = ? ORDER BY created_at",
            (game_id,),
        )

        return [
            Bet(
                bet_id=row["bet_id"],
                game_id=row["game_id"],
                bettor_id=row["bettor_id"],
                bet_type=BetType(row["bet_type"]),
                target=row["target"],
                amount=Decimal(str(row["amount"])),
                round_placed=row["round_placed"],
                weight=Decimal(str(row["weight"])),
            )
            for row in rows
        ]

    async def settle_bets(self, game_id: str, payouts: dict[str, Decimal]) -> None:
        """Settle bets for a completed game."""
        for bet_id, payout in payouts.items():
            await self._db.execute(
                "UPDATE bets SET settled = 1, payout = ? WHERE bet_id = ?",
                (float(payout), bet_id),
            )
        await self._db.commit()
