"""Contract interaction wrapper for oracle operations."""

from src.blockchain.provider import BlockchainProvider
from src.utils.logger import get_logger

log = get_logger(__name__)


class MafiaBettingContract:
    """Wraps MafiaBetting contract for oracle operations."""

    def __init__(self, provider: BlockchainProvider):
        """Initialize contract wrapper.

        Args:
            provider: Blockchain provider instance.
        """
        self.provider = provider

    async def create_game(self, game_id: int) -> str:
        """Create a new game on-chain.

        Args:
            game_id: Unique game identifier (uint256).

        Returns:
            Transaction hash as hex string.
        """
        contract = await self.provider.get_contract()
        tx = contract.functions.createGame(game_id).build_transaction(
            {
                "from": self.provider.account.address,
                "nonce": await self.provider.w3.eth.get_transaction_count(
                    self.provider.account.address
                ),
                "gas": 100000,
                "gasPrice": self.provider.w3.eth.gas_price,
            }
        )
        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(
            signed.raw_transaction
        )
        receipt = await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)
        log.info("game_created_onchain", game_id=game_id, tx_hash=tx_hash.hex())
        return tx_hash.hex()

    async def lock_betting(self, game_id: int) -> str:
        """Lock betting for a game.

        Args:
            game_id: Game identifier.

        Returns:
            Transaction hash as hex string.
        """
        contract = await self.provider.get_contract()
        tx = contract.functions.lockBetting(game_id).build_transaction(
            {
                "from": self.provider.account.address,
                "nonce": await self.provider.w3.eth.get_transaction_count(
                    self.provider.account.address
                ),
                "gas": 60000,
                "gasPrice": self.provider.w3.eth.gas_price,
            }
        )
        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(
            signed.raw_transaction
        )
        await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)
        log.info("betting_locked_onchain", game_id=game_id, tx_hash=tx_hash.hex())
        return tx_hash.hex()

    async def settle(self, game_id: int, mafia_won: bool) -> str:
        """Settle game outcome on-chain.

        Args:
            game_id: Game identifier.
            mafia_won: True if mafia won, False if citizens won.

        Returns:
            Transaction hash as hex string.
        """
        contract = await self.provider.get_contract()
        tx = contract.functions.settle(game_id, mafia_won).build_transaction(
            {
                "from": self.provider.account.address,
                "nonce": await self.provider.w3.eth.get_transaction_count(
                    self.provider.account.address
                ),
                "gas": 120000,
                "gasPrice": self.provider.w3.eth.gas_price,
            }
        )
        signed = self.provider.account.sign_transaction(tx)
        tx_hash = await self.provider.w3.eth.send_raw_transaction(
            signed.raw_transaction
        )
        await self.provider.w3.eth.wait_for_transaction_receipt(tx_hash)
        log.info(
            "game_settled_onchain", game_id=game_id, mafia_won=mafia_won, tx_hash=tx_hash.hex()
        )
        return tx_hash.hex()

    async def get_game(self, game_id: int) -> dict:
        """Get game state from contract.

        Args:
            game_id: Game identifier.

        Returns:
            Dictionary with game state fields.
        """
        contract = await self.provider.get_contract()
        game = await contract.functions.getGame(game_id).call()
        return {
            "exists": game[0],
            "locked": game[1],
            "settled": game[2],
            "mafiaWon": game[3],
            "mafiaPool": game[4],
            "citizenPool": game[5],
            "totalPool": game[6],
        }
