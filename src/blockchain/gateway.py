"""Unified blockchain gateway for V2 contract interactions."""
import os
from decimal import Decimal

from web3 import Web3

from src.blockchain.provider import BlockchainProvider
from src.config.constants import Role
from src.utils.logger import get_logger

log = get_logger(__name__)


def uuid_to_bytes32(uuid_str: str) -> bytes:
    """Convert UUID string to bytes32.

    Strips hyphens and pads to 32 bytes.
    """
    hex_str = uuid_str.replace("-", "")
    return bytes.fromhex(hex_str.ljust(64, "0"))


def compute_role_hash(role_map: dict[str, Role]) -> bytes:
    """Compute deterministic keccak256 hash of role assignments.

    Sorts by player name for determinism.
    """
    # Sort by name for deterministic ordering
    sorted_items = sorted(role_map.items())
    # Encode as "name:role" pairs joined by "|"
    role_string = "|".join(f"{name}:{role.value}" for name, role in sorted_items)
    return Web3.keccak(text=role_string)


def compute_commitment(role_hash: bytes, secret: bytes) -> bytes:
    """Compute keccak256(abi.encodePacked(roleHash, secret)).

    Must match Solidity's keccak256(abi.encodePacked(roleHash, secret)).
    """
    return Web3.keccak(role_hash + secret)


class BlockchainGateway:
    """Unified Python interface for V2 contract operations."""

    def __init__(self, provider: BlockchainProvider):
        self.provider = provider
        self._secrets: dict[str, bytes] = {}  # game_id -> random secret

    async def commit_roles(self, game_id: str, role_map: dict[str, Role]) -> str:
        """Create game on-chain with role commitment.

        Generates a random secret, computes commitment, calls createGame.
        Stores secret for later reveal during settlement.

        Args:
            game_id: UUID game identifier.
            role_map: Dict of player_name -> Role.

        Returns:
            Transaction hash as hex string.
        """
        secret = os.urandom(32)
        role_hash = compute_role_hash(role_map)
        commitment = compute_commitment(role_hash, secret)

        # Store secret for settlement
        self._secrets[game_id] = secret

        game_id_bytes = uuid_to_bytes32(game_id)

        contract = await self.provider.get_contract(version="v2")
        tx = await contract.functions.createGame(
            game_id_bytes, commitment
        ).build_transaction({
            "from": self.provider.account.address,
            "nonce": await self.provider.w3.eth.get_transaction_count(
                self.provider.account.address
            ),
            "gas": 150000,
            "gasPrice": self.provider.w3.eth.gas_price,
        })

        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(signed.raw_transaction)
        await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)

        log.info("v2_game_created", game_id=game_id, tx_hash=tx_hash.hex())
        return tx_hash.hex()

    async def lock_betting(self, game_id: str) -> str:
        """Lock betting for a game.

        Args:
            game_id: UUID game identifier.

        Returns:
            Transaction hash as hex string.
        """
        game_id_bytes = uuid_to_bytes32(game_id)

        contract = await self.provider.get_contract(version="v2")
        tx = await contract.functions.lockBetting(
            game_id_bytes
        ).build_transaction({
            "from": self.provider.account.address,
            "nonce": await self.provider.w3.eth.get_transaction_count(
                self.provider.account.address
            ),
            "gas": 60000,
            "gasPrice": self.provider.w3.eth.gas_price,
        })

        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(signed.raw_transaction)
        await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)

        log.info("v2_betting_locked", game_id=game_id, tx_hash=tx_hash.hex())
        return tx_hash.hex()

    async def settle_game(
        self,
        game_id: str,
        role_map: dict[str, Role],
        winners: list[str],
        amounts: list[Decimal],
    ) -> str:
        """Settle game on-chain with commit-reveal.

        Recomputes role_hash, retrieves stored secret, converts amounts
        to raw USDC (6 decimals), calls settle with verification.

        Args:
            game_id: UUID game identifier.
            role_map: Dict of player_name -> Role.
            winners: List of winner wallet addresses.
            amounts: List of payout amounts in USDC (human-readable).

        Returns:
            Transaction hash as hex string.
        """
        secret = self._secrets.get(game_id)
        if not secret:
            raise ValueError(f"No secret stored for game {game_id}")

        role_hash = compute_role_hash(role_map)
        game_id_bytes = uuid_to_bytes32(game_id)

        # Validate amounts before conversion
        for amount in amounts:
            if amount < Decimal("0"):
                raise ValueError(f"Settlement amount cannot be negative: {amount}")
            if amount > Decimal("1000000"):  # 1M USDC cap
                raise ValueError(f"Settlement amount exceeds maximum: {amount}")

        # Convert amounts to raw USDC (6 decimals)
        raw_amounts = [int(amount * Decimal("1000000")) for amount in amounts]

        contract = await self.provider.get_contract(version="v2")
        tx = await contract.functions.settle(
            game_id_bytes, role_hash, secret, winners, raw_amounts
        ).build_transaction({
            "from": self.provider.account.address,
            "nonce": await self.provider.w3.eth.get_transaction_count(
                self.provider.account.address
            ),
            "gas": 300000,
            "gasPrice": self.provider.w3.eth.gas_price,
        })

        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(signed.raw_transaction)
        await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)

        # Clean up stored secret
        del self._secrets[game_id]

        log.info("v2_game_settled", game_id=game_id, tx_hash=tx_hash.hex())
        return tx_hash.hex()
