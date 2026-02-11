"""Web3 provider for Monad blockchain connection."""

import json
from pathlib import Path

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware

from src.utils.logger import get_logger

log = get_logger(__name__)


class BlockchainProvider:
    """Manages Web3 connection and contract instance."""

    def __init__(self, rpc_url: str, private_key: str, contract_address: str):
        """Initialize blockchain provider.

        Args:
            rpc_url: Monad testnet RPC endpoint.
            private_key: Private key for signing transactions.
            contract_address: Deployed MafiaBetting contract address.
        """
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        # Monad may need POA middleware
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        self.account = self.w3.eth.account.from_key(private_key)
        self.contract_address = contract_address
        self._contract = None

    async def get_contract(self):
        """Load contract ABI and return contract instance.

        Returns:
            Web3 contract instance for MafiaBetting.
        """
        if self._contract is None:
            abi_path = (
                Path(__file__).parent.parent.parent
                / "artifacts"
                / "contracts"
                / "MafiaBetting.sol"
                / "MafiaBetting.json"
            )
            with open(abi_path) as f:
                artifact = json.load(f)
            self._contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.contract_address),
                abi=artifact["abi"],
            )
        return self._contract

    async def is_connected(self) -> bool:
        """Check if connected to blockchain.

        Returns:
            True if connected, False otherwise.
        """
        try:
            return await self.w3.is_connected()
        except Exception:
            return False
