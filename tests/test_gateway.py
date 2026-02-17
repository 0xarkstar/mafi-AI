"""Tests for blockchain gateway module."""
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from web3 import Web3

from src.blockchain.gateway import (
    BlockchainGateway,
    compute_commitment,
    compute_role_hash,
    uuid_to_bytes32,
)
from src.config.constants import Role


class TestUuidToBytes32:
    """Tests for uuid_to_bytes32 helper."""

    def test_standard_uuid(self):
        """Test conversion of standard UUID."""
        result = uuid_to_bytes32("550e8400-e29b-41d4-a716-446655440000")
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_strips_hyphens(self):
        """Test hyphens are removed."""
        result = uuid_to_bytes32("12345678-1234-1234-1234-123456789abc")
        assert b"-" not in result

    def test_deterministic(self):
        """Same UUID always produces same bytes."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert uuid_to_bytes32(uuid) == uuid_to_bytes32(uuid)

    def test_different_uuids_differ(self):
        """Different UUIDs produce different bytes."""
        a = uuid_to_bytes32("550e8400-e29b-41d4-a716-446655440000")
        b = uuid_to_bytes32("660f9500-f39c-52e5-b827-557766550111")
        assert a != b


class TestComputeRoleHash:
    """Tests for compute_role_hash helper."""

    def test_deterministic(self):
        """Same role_map always produces same hash."""
        role_map = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}
        assert compute_role_hash(role_map) == compute_role_hash(role_map)

    def test_order_independent(self):
        """Role hash is order-independent (sorted internally)."""
        map1 = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}
        map2 = {"Bob": Role.CITIZEN, "Alice": Role.MAFIA}
        assert compute_role_hash(map1) == compute_role_hash(map2)

    def test_different_roles_differ(self):
        """Different role assignments produce different hashes."""
        map1 = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}
        map2 = {"Alice": Role.CITIZEN, "Bob": Role.MAFIA}
        assert compute_role_hash(map1) != compute_role_hash(map2)

    def test_returns_bytes(self):
        """Returns bytes type."""
        result = compute_role_hash({"Alice": Role.MAFIA})
        assert isinstance(result, bytes)
        assert len(result) == 32


class TestComputeCommitment:
    """Tests for compute_commitment helper."""

    def test_deterministic(self):
        """Same inputs produce same commitment."""
        role_hash = b"\x01" * 32
        secret = b"\x02" * 32
        assert compute_commitment(role_hash, secret) == compute_commitment(role_hash, secret)

    def test_different_secrets_differ(self):
        """Different secrets produce different commitments."""
        role_hash = b"\x01" * 32
        c1 = compute_commitment(role_hash, b"\x02" * 32)
        c2 = compute_commitment(role_hash, b"\x03" * 32)
        assert c1 != c2

    def test_matches_web3_keccak(self):
        """Commitment matches Web3.keccak(roleHash + secret)."""
        role_hash = b"\x01" * 32
        secret = b"\x02" * 32
        expected = Web3.keccak(role_hash + secret)
        assert compute_commitment(role_hash, secret) == expected


class TestBlockchainGateway:
    """Tests for BlockchainGateway class."""

    def _make_mock_provider(self):
        """Create a mock provider with all required attributes."""
        mock_provider = MagicMock()
        mock_provider.account = MagicMock()
        mock_provider.account.address = "0x1234"
        mock_provider.account.sign_transaction = MagicMock(
            return_value=MagicMock(raw_transaction=b"raw_tx")
        )
        mock_provider.w3 = MagicMock()
        mock_provider.w3.eth = MagicMock()
        mock_provider.w3.eth.get_transaction_count = AsyncMock(return_value=0)
        mock_provider.w3.eth.gas_price = 1000000000
        mock_provider.w3.eth.send_raw_transaction = AsyncMock(return_value=b"\xab\xcd\xef")
        mock_provider.w3.eth.wait_for_transaction_receipt = AsyncMock(return_value={})
        return mock_provider

    def _make_mock_contract(self, function_name):
        """Create a mock contract with a specific function."""
        mock_contract = MagicMock()
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction = AsyncMock(return_value={"gas": 150000})
        getattr(mock_contract.functions, function_name).return_value = mock_tx_builder
        return mock_contract

    @pytest.mark.asyncio
    async def test_commit_roles_returns_tx_hash(self):
        """Test commit_roles returns a hex transaction hash."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("createGame")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        role_map = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}

        tx_hash = await gateway.commit_roles("550e8400-e29b-41d4-a716-446655440000", role_map)

        assert isinstance(tx_hash, str)
        assert len(tx_hash) > 0

    @pytest.mark.asyncio
    async def test_commit_roles_stores_secret(self):
        """Test commit_roles stores the secret for later reveal."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("createGame")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        game_id = "550e8400-e29b-41d4-a716-446655440000"
        role_map = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}

        await gateway.commit_roles(game_id, role_map)

        assert game_id in gateway._secrets
        assert len(gateway._secrets[game_id]) == 32

    @pytest.mark.asyncio
    async def test_commit_roles_calls_create_game_v2(self):
        """Test commit_roles uses v2 contract."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("createGame")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        role_map = {"Alice": Role.MAFIA}

        await gateway.commit_roles("550e8400-e29b-41d4-a716-446655440000", role_map)

        mock_provider.get_contract.assert_called_once_with(version="v2")

    @pytest.mark.asyncio
    async def test_lock_betting_returns_tx_hash(self):
        """Test lock_betting returns a hex transaction hash."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("lockBetting")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        tx_hash = await gateway.lock_betting("550e8400-e29b-41d4-a716-446655440000")

        assert isinstance(tx_hash, str)

    @pytest.mark.asyncio
    async def test_lock_betting_calls_v2_contract(self):
        """Test lock_betting uses v2 contract."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("lockBetting")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        await gateway.lock_betting("550e8400-e29b-41d4-a716-446655440000")

        mock_provider.get_contract.assert_called_once_with(version="v2")

    @pytest.mark.asyncio
    async def test_settle_game_returns_tx_hash(self):
        """Test settle_game returns a hex transaction hash."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("settle")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        game_id = "550e8400-e29b-41d4-a716-446655440000"
        role_map = {"Alice": Role.MAFIA, "Bob": Role.CITIZEN}

        # Pre-store a secret as if commit_roles was called
        gateway._secrets[game_id] = b"\x42" * 32

        tx_hash = await gateway.settle_game(
            game_id,
            role_map,
            winners=["0xwinner1"],
            amounts=[Decimal("10.5")],
        )

        assert isinstance(tx_hash, str)

    @pytest.mark.asyncio
    async def test_settle_game_cleans_up_secret(self):
        """Test settle_game removes secret after settlement."""
        mock_provider = self._make_mock_provider()
        mock_contract = self._make_mock_contract("settle")
        mock_provider.get_contract = AsyncMock(return_value=mock_contract)

        gateway = BlockchainGateway(mock_provider)
        game_id = "550e8400-e29b-41d4-a716-446655440000"
        role_map = {"Alice": Role.MAFIA}

        gateway._secrets[game_id] = b"\x42" * 32

        await gateway.settle_game(game_id, role_map, winners=[], amounts=[])

        assert game_id not in gateway._secrets

    @pytest.mark.asyncio
    async def test_settle_game_raises_without_secret(self):
        """Test settle_game raises ValueError if no secret stored."""
        mock_provider = self._make_mock_provider()
        gateway = BlockchainGateway(mock_provider)

        with pytest.raises(ValueError, match="No secret stored"):
            await gateway.settle_game(
                "nonexistent-game-id",
                {},
                winners=[],
                amounts=[],
            )

    @pytest.mark.asyncio
    async def test_relay_bet_returns_none(self):
        """Test relay_bet placeholder returns None."""
        mock_provider = self._make_mock_provider()
        gateway = BlockchainGateway(mock_provider)

        result = await gateway.relay_bet(game_id="test", bettor="0x1234", amount=Decimal("5"))

        assert result is None
