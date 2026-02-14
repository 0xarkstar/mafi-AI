"""USDC settlement via web3.py."""

from decimal import Decimal

import structlog
from web3 import AsyncWeb3
from web3.types import TxParams

logger = structlog.get_logger(__name__)


class USDCSettlement:
    """Handles USDC payouts to winners via web3.py."""

    # Minimal ERC-20 ABI for transfer()
    ERC20_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
    ]

    def __init__(self, w3: AsyncWeb3, usdc_address: str, private_key: str):
        """Initialize USDC settlement.

        Args:
            w3: AsyncWeb3 instance (connected to Monad testnet).
            usdc_address: USDC contract address on Monad.
            private_key: Server wallet private key (0x...).
        """
        self.w3 = w3
        self.account = w3.eth.account.from_key(private_key)
        self.usdc = w3.eth.contract(
            address=w3.to_checksum_address(usdc_address), abi=self.ERC20_ABI
        )

        logger.info(
            "usdc_settlement_initialized",
            server_wallet=self.account.address,
            usdc_address=usdc_address,
        )

    async def settle_payouts(self, payouts: dict[str, Decimal]) -> list[dict]:
        """Transfer USDC to each winner.

        Args:
            payouts: Dict of wallet_address → payout_usdc.

        Returns:
            List of dicts with keys: address, amount, tx_hash for each successful transfer.
        """
        results = []

        for address, amount in payouts.items():
            try:
                # Convert USDC amount to raw units (6 decimals)
                amount_raw = int(amount * Decimal("1000000"))

                if amount_raw <= 0:
                    logger.warning("skipping_zero_payout", address=address)
                    continue

                # Build transaction
                tx: TxParams = await self.usdc.functions.transfer(
                    self.w3.to_checksum_address(address), amount_raw
                ).build_transaction(
                    {
                        "from": self.account.address,
                        "nonce": await self.w3.eth.get_transaction_count(
                            self.account.address
                        ),
                        "gas": 100000,  # Estimated gas for ERC-20 transfer
                        "gasPrice": await self.w3.eth.gas_price,
                    }
                )

                # Sign transaction
                signed_tx = self.account.sign_transaction(tx)

                # Send transaction
                tx_hash = await self.w3.eth.send_raw_transaction(
                    signed_tx.raw_transaction
                )

                # Wait for receipt
                receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt["status"] == 1:
                    logger.info(
                        "usdc_transfer_success",
                        to=address,
                        amount=float(amount),
                        tx_hash=tx_hash.hex(),
                    )
                    results.append(
                        {
                            "address": address,
                            "amount": float(amount),
                            "tx_hash": tx_hash.hex(),
                        }
                    )
                else:
                    logger.error(
                        "usdc_transfer_failed",
                        to=address,
                        amount=float(amount),
                        tx_hash=tx_hash.hex(),
                    )

            except Exception as exc:
                logger.error(
                    "usdc_transfer_error", to=address, amount=float(amount), error=str(exc)
                )

        logger.info("usdc_settlement_complete", total_transfers=len(results))

        return results

    async def get_balance(self) -> Decimal:
        """Get server wallet USDC balance.

        Returns:
            Server wallet balance in USDC (converted from raw units).
        """
        try:
            balance_raw = await self.usdc.functions.balanceOf(
                self.account.address
            ).call()
            balance_usdc = Decimal(balance_raw) / Decimal("1000000")

            logger.info("server_usdc_balance", balance=float(balance_usdc))

            return balance_usdc

        except Exception as exc:
            logger.error("balance_check_failed", error=str(exc))
            return Decimal("0")
