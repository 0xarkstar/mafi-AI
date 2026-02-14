"""Tests for USDC settlement via web3.py."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.betting.settlement import USDCSettlement


class TestUSDCSettlement:
    """Tests for USDCSettlement class."""

    @pytest.fixture
    def mock_w3(self):
        """Create mock AsyncWeb3 instance."""
        w3 = MagicMock()
        w3.to_checksum_address = lambda addr: addr  # Passthrough for testing

        # Mock account
        mock_account = MagicMock()
        mock_account.address = "0xServerWallet"
        w3.eth.account.from_key = MagicMock(return_value=mock_account)

        # Mock contract
        mock_contract = MagicMock()
        w3.eth.contract = MagicMock(return_value=mock_contract)

        # Mock gas price (needs to be awaitable property that returns fresh coroutine each time)
        async def mock_gas_price():
            return 1000000000  # 1 gwei

        # Use PropertyMock to create new coroutine on each access
        type(w3.eth).gas_price = property(lambda self: mock_gas_price())

        # Mock transaction count (async method)
        w3.eth.get_transaction_count = AsyncMock(return_value=42)

        # Mock send_raw_transaction (returns HexBytes-like object)
        mock_tx_hash = MagicMock()
        mock_tx_hash.hex.return_value = "0xtxhash123"
        w3.eth.send_raw_transaction = AsyncMock(return_value=mock_tx_hash)

        # Mock wait_for_transaction_receipt
        w3.eth.wait_for_transaction_receipt = AsyncMock(
            return_value={"status": 1}  # Success
        )

        return w3

    @pytest.mark.asyncio
    async def test_settle_payouts_single_winner(self, mock_w3):
        """Test settling payout to single winner."""
        # Create settlement instance
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer function chain properly
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(
            return_value={
                "from": "0xServerWallet",
                "nonce": 42,
                "gas": 100000,
                "gasPrice": 1000000000,
            }
        )
        settlement.usdc.functions.transfer.return_value = mock_transfer

        # Mock sign_transaction
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"signed_tx_data"
        settlement.account.sign_transaction = MagicMock(return_value=mock_signed)

        # Create payouts
        payouts = {"0xWinner1": Decimal("50.00")}

        # Settle
        results = await settlement.settle_payouts(payouts)

        # Verify results
        assert len(results) == 1
        assert results[0]["address"] == "0xWinner1"
        assert results[0]["amount"] == 50.0
        assert results[0]["tx_hash"] == "0xtxhash123"

        # Verify transfer was called with correct amount (50 USDC = 50000000 raw units)
        settlement.usdc.functions.transfer.assert_called_once_with(
            "0xWinner1", 50000000
        )

    @pytest.mark.asyncio
    async def test_settle_payouts_multiple_winners(self, mock_w3):
        """Test settling payouts to multiple winners."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer function chain properly
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(
            return_value={
                "from": "0xServerWallet",
                "nonce": 42,
                "gas": 100000,
                "gasPrice": 1000000000,
            }
        )
        settlement.usdc.functions.transfer.return_value = mock_transfer

        # Mock sign_transaction
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"signed_tx_data"
        settlement.account.sign_transaction = MagicMock(return_value=mock_signed)

        # Mock tx hash counter
        tx_hashes = [b"0xtx1", b"0xtx2", b"0xtx3"]
        mock_w3.eth.send_raw_transaction = AsyncMock(side_effect=tx_hashes)

        # Create payouts
        payouts = {
            "0xWinner1": Decimal("50.00"),
            "0xWinner2": Decimal("30.50"),
            "0xWinner3": Decimal("19.50"),
        }

        # Settle
        results = await settlement.settle_payouts(payouts)

        # Verify results
        assert len(results) == 3
        assert results[0]["address"] == "0xWinner1"
        assert results[0]["amount"] == 50.0
        assert results[1]["address"] == "0xWinner2"
        assert results[1]["amount"] == 30.5
        assert results[2]["address"] == "0xWinner3"
        assert results[2]["amount"] == 19.5

        # Verify all transfers called
        assert settlement.usdc.functions.transfer.call_count == 3

    @pytest.mark.asyncio
    async def test_settle_payouts_skips_zero_amount(self, mock_w3):
        """Test that zero payouts are skipped."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer function
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(return_value={})
        settlement.usdc.functions.transfer = MagicMock(return_value=mock_transfer)

        # Create payouts with zero
        payouts = {
            "0xWinner1": Decimal("50.00"),
            "0xWinner2": Decimal("0.00"),  # Should be skipped
        }

        # Settle
        results = await settlement.settle_payouts(payouts)

        # Verify only 1 transfer made
        assert len(results) == 1
        assert results[0]["address"] == "0xWinner1"

        # Verify transfer only called once (not for zero amount)
        assert settlement.usdc.functions.transfer.call_count == 1

    @pytest.mark.asyncio
    async def test_settle_payouts_skips_negative_amount(self, mock_w3):
        """Test that negative payouts are skipped."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Create payouts with negative (shouldn't happen but defensive)
        payouts = {
            "0xWinner1": Decimal("-10.00"),  # Should be skipped
        }

        # Settle
        results = await settlement.settle_payouts(payouts)

        # Verify no transfers made
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_settle_payouts_transfer_failure(self, mock_w3):
        """Test handling of transfer failure."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer function chain properly
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(
            return_value={
                "from": "0xServerWallet",
                "nonce": 42,
                "gas": 100000,
                "gasPrice": 1000000000,
            }
        )
        settlement.usdc.functions.transfer.return_value = mock_transfer

        # Mock sign_transaction
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"signed_tx_data"
        settlement.account.sign_transaction = MagicMock(return_value=mock_signed)

        # Mock receipt with status=0 (failure)
        mock_w3.eth.wait_for_transaction_receipt = AsyncMock(
            return_value={"status": 0}
        )

        # Create payouts
        payouts = {"0xWinner1": Decimal("50.00")}

        # Settle
        results = await settlement.settle_payouts(payouts)

        # Verify no results (transfer failed)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_settle_payouts_exception_handling(self, mock_w3):
        """Test that exceptions during transfer are logged but don't crash."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer to raise exception
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(
            side_effect=Exception("Transfer failed")
        )
        settlement.usdc.functions.transfer = MagicMock(return_value=mock_transfer)

        # Create payouts
        payouts = {
            "0xWinner1": Decimal("50.00"),
            "0xWinner2": Decimal("30.00"),  # This should still be attempted
        }

        # Settle (should not raise exception)
        results = await settlement.settle_payouts(payouts)

        # Verify both failed (no results)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_balance_success(self, mock_w3):
        """Test getting server wallet USDC balance."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock balanceOf
        mock_balance_of = MagicMock()
        mock_balance_of.call = AsyncMock(return_value=100000000)  # 100 USDC (6 decimals)
        settlement.usdc.functions.balanceOf = MagicMock(return_value=mock_balance_of)

        # Get balance
        balance = await settlement.get_balance()

        # Verify balance converted correctly
        assert balance == Decimal("100.00")

        # Verify balanceOf called with server address
        settlement.usdc.functions.balanceOf.assert_called_once_with("0xServerWallet")

    @pytest.mark.asyncio
    async def test_get_balance_zero(self, mock_w3):
        """Test getting zero balance."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock balanceOf returning 0
        mock_balance_of = MagicMock()
        mock_balance_of.call = AsyncMock(return_value=0)
        settlement.usdc.functions.balanceOf = MagicMock(return_value=mock_balance_of)

        # Get balance
        balance = await settlement.get_balance()

        # Verify zero balance
        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_balance_error_handling(self, mock_w3):
        """Test get_balance returns 0 on error."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock balanceOf to raise exception
        mock_balance_of = MagicMock()
        mock_balance_of.call = AsyncMock(side_effect=Exception("RPC error"))
        settlement.usdc.functions.balanceOf = MagicMock(return_value=mock_balance_of)

        # Get balance (should not raise)
        balance = await settlement.get_balance()

        # Verify returns 0 on error
        assert balance == Decimal("0")

    @pytest.mark.asyncio
    async def test_decimal_precision(self, mock_w3):
        """Test that decimal amounts are handled precisely."""
        settlement = USDCSettlement(
            w3=mock_w3,
            usdc_address="0xUSDC",
            private_key="0xprivatekey",
        )

        # Mock transfer function
        mock_transfer = MagicMock()
        mock_transfer.build_transaction = AsyncMock(return_value={})
        settlement.usdc.functions.transfer = MagicMock(return_value=mock_transfer)

        # Mock sign_transaction
        mock_signed = MagicMock()
        mock_signed.raw_transaction = b"signed_tx_data"
        settlement.account.sign_transaction = MagicMock(return_value=mock_signed)

        # Create payout with precise decimal
        payouts = {"0xWinner1": Decimal("12.345678")}

        # Settle
        await settlement.settle_payouts(payouts)

        # Verify transfer called with correctly rounded amount
        # 12.345678 USDC = 12345678 raw units (6 decimals, truncated)
        settlement.usdc.functions.transfer.assert_called_once_with(
            "0xWinner1", 12345678
        )
