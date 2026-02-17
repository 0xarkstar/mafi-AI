"""Web3 provider for Monad blockchain connection."""

import json
from pathlib import Path

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware

from src.utils.logger import get_logger

log = get_logger(__name__)


async def create_web3_provider(rpc_url: str, chain_id: int) -> AsyncWeb3:
    """Factory for standalone AsyncWeb3 instance with POA middleware.

    Args:
        rpc_url: RPC endpoint URL.
        chain_id: Chain ID (used for validation only).

    Returns:
        Connected AsyncWeb3 instance.

    Raises:
        ConnectionError: If unable to connect to the RPC endpoint.
    """
    w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not await w3.is_connected():
        raise ConnectionError(f"Cannot connect to {rpc_url}")
    return w3


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
        self._contracts: dict = {}
        self._contract = None  # backward compat alias for _contracts["v1"]

    async def get_contract(self, version: str = "v1"):
        """Load contract ABI and return contract instance.

        Args:
            version: Contract version, "v1" or "v2". Defaults to "v1".

        Returns:
            Web3 contract instance for the specified contract version.
        """
        if version not in self._contracts:
            if version == "v2":
                abi_path = (
                    Path(__file__).parent.parent.parent
                    / "artifacts"
                    / "contracts"
                    / "MafiaBettingV2.sol"
                    / "MafiaBettingV2.json"
                )
            else:
                abi_path = (
                    Path(__file__).parent.parent.parent
                    / "artifacts"
                    / "contracts"
                    / "MafiaBetting.sol"
                    / "MafiaBetting.json"
                )
            with open(abi_path) as f:
                artifact = json.load(f)
            self._contracts[version] = self.w3.eth.contract(
                address=self.w3.to_checksum_address(self.contract_address),
                abi=artifact["abi"],
            )
        return self._contracts[version]

    async def is_connected(self) -> bool:
        """Check if connected to blockchain.

        Returns:
            True if connected, False otherwise.
        """
        try:
            return await self.w3.is_connected()
        except Exception:
            return False
