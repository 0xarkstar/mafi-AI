"""Server-side demo balance tracking."""
from decimal import Decimal

from src.utils.logger import get_logger

log = get_logger(__name__)
INITIAL_BALANCE = Decimal("50.0")


class BalanceManager:
    """Tracks demo USDC balances per wallet address (in-memory)."""

    def __init__(self, initial: Decimal = INITIAL_BALANCE):
        self._balances: dict[str, Decimal] = {}
        self._initial = initial

    def get_balance(self, addr: str) -> Decimal:
        return self._balances.setdefault(addr, self._initial)

    def deduct(self, addr: str, amount: Decimal) -> bool:
        bal = self.get_balance(addr)
        if amount > bal:
            return False
        self._balances[addr] = bal - amount
        return True

    def credit(self, addr: str, amount: Decimal) -> None:
        self._balances[addr] = self.get_balance(addr) + amount

    def reset(self) -> None:
        self._balances.clear()
