"""Tests for blockchain integration module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.blockchain.contract import MafiaBettingContract
from src.blockchain.provider import BlockchainProvider


class TestBlockchainProvider:
    """Tests for BlockchainProvider."""

    def test_init(self):
        """Test provider initialization."""
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3:
            mock_web3.return_value = MagicMock()
            mock_web3.return_value.middleware_onion = MagicMock()
            mock_web3.return_value.eth = MagicMock()
            mock_web3.return_value.eth.account = MagicMock()
            provider = BlockchainProvider(
                rpc_url="https://testnet-rpc.monad.xyz",
                private_key="0x" + "a" * 64,
                contract_address="0x" + "b" * 40,
            )
            assert provider.contract_address == "0x" + "b" * 40
            assert provider._contract is None

    @pytest.mark.asyncio
    async def test_is_connected_true(self):
        """Test is_connected returns True when connected."""
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3:
            instance = MagicMock()
            instance.middleware_onion = MagicMock()
            instance.eth = MagicMock()
            instance.eth.account = MagicMock()
            instance.is_connected = AsyncMock(return_value=True)
            mock_web3.return_value = instance
            provider = BlockchainProvider(
                "https://rpc", "0x" + "a" * 64, "0x" + "b" * 40
            )
            assert await provider.is_connected() is True

    @pytest.mark.asyncio
    async def test_is_connected_false_on_error(self):
        """Test is_connected returns False on exception."""
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3:
            instance = MagicMock()
            instance.middleware_onion = MagicMock()
            instance.eth = MagicMock()
            instance.eth.account = MagicMock()
            instance.is_connected = AsyncMock(side_effect=Exception("connection failed"))
            mock_web3.return_value = instance
            provider = BlockchainProvider(
                "https://rpc", "0x" + "a" * 64, "0x" + "b" * 40
            )
            assert await provider.is_connected() is False


class TestMafiaBettingContract:
    """Tests for MafiaBettingContract."""

    @pytest.mark.asyncio
    async def test_create_game(self):
        """Test create_game builds and sends transaction."""
        mock_provider = MagicMock()
        mock_contract = MagicMock()

        # Set up the function call chain
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction = AsyncMock(return_value={"gas": 100000})
        mock_contract.functions.createGame.return_value = mock_tx_builder

        mock_provider.get_contract = AsyncMock(return_value=mock_contract)
        mock_provider.account = MagicMock()
        mock_provider.account.address = "0x1234"
        mock_provider.account.sign_transaction = MagicMock(
            return_value=MagicMock(raw_transaction=b"raw")
        )
        mock_provider.w3 = MagicMock()
        mock_provider.w3.eth = MagicMock()
        mock_provider.w3.eth.get_transaction_count = AsyncMock(return_value=0)
        mock_provider.w3.eth.gas_price = 1000000000
        mock_provider.w3.eth.send_raw_transaction = AsyncMock(return_value=b"\x12\x34")
        mock_provider.w3.eth.wait_for_transaction_receipt = AsyncMock(return_value={})

        contract = MafiaBettingContract(mock_provider)
        tx_hash = await contract.create_game(12345)
        assert isinstance(tx_hash, str)
        mock_contract.functions.createGame.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_settle(self):
        """Test settle builds and sends transaction."""
        mock_provider = MagicMock()
        mock_contract = MagicMock()

        # Set up the function call chain
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction = AsyncMock(return_value={"gas": 120000})
        mock_contract.functions.settle.return_value = mock_tx_builder

        mock_provider.get_contract = AsyncMock(return_value=mock_contract)
        mock_provider.account = MagicMock()
        mock_provider.account.address = "0x1234"
        mock_provider.account.sign_transaction = MagicMock(
            return_value=MagicMock(raw_transaction=b"raw")
        )
        mock_provider.w3 = MagicMock()
        mock_provider.w3.eth = MagicMock()
        mock_provider.w3.eth.get_transaction_count = AsyncMock(return_value=1)
        mock_provider.w3.eth.gas_price = 1000000000
        mock_provider.w3.eth.send_raw_transaction = AsyncMock(return_value=b"\x56\x78")
        mock_provider.w3.eth.wait_for_transaction_receipt = AsyncMock(return_value={})

        contract = MafiaBettingContract(mock_provider)
        tx_hash = await contract.settle(12345, True)
        assert isinstance(tx_hash, str)
        mock_contract.functions.settle.assert_called_once_with(12345, True)


class TestGameEngineBlockchain:
    """Tests for GameEngine blockchain integration."""

    def test_uuid_to_uint256(self):
        """Test UUID to uint256 conversion."""
        from src.engine.game_engine import GameEngine

        engine = object.__new__(GameEngine)
        result = engine._uuid_to_uint256("550e8400-e29b-41d4-a716-446655440000")
        assert isinstance(result, int)
        assert result < 2**64

    def test_uuid_to_uint256_deterministic(self):
        """Test same UUID always produces same uint256."""
        from src.engine.game_engine import GameEngine

        engine = object.__new__(GameEngine)
        uuid = "12345678-1234-1234-1234-123456789abc"
        assert engine._uuid_to_uint256(uuid) == engine._uuid_to_uint256(uuid)


class TestBlockchainConfigEndpoint:
    """Tests for /api/blockchain-config endpoint."""

    def test_blockchain_config_disabled(self):
        """Test /api/blockchain-config when blockchain disabled."""
        from unittest.mock import MagicMock

        from fastapi.testclient import TestClient

        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.config.settings import Settings

        settings = MagicMock(spec=Settings)
        settings.blockchain_enabled = False
        settings.blockchain_contract_address = ""
        settings.blockchain_chain_id = 0
        settings.blockchain_rpc_url = ""
        settings.port = 8080
        settings.host = "0.0.0.0"
        settings.x402_enabled = False
        settings.ai_bettor_enabled = False

        app = create_app(settings, WSManager())
        client = TestClient(app)
        response = client.get("/api/blockchain-config")
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_blockchain_config_enabled(self):
        """Test /api/blockchain-config when blockchain enabled."""
        from unittest.mock import MagicMock

        from fastapi.testclient import TestClient

        from src.api.server import create_app
        from src.api.ws_manager import WSManager
        from src.config.settings import Settings

        settings = MagicMock(spec=Settings)
        settings.blockchain_enabled = True
        settings.blockchain_contract_address = "0x1234"
        settings.blockchain_chain_id = 10143
        settings.blockchain_rpc_url = "https://testnet-rpc.monad.xyz"
        settings.port = 8080
        settings.host = "0.0.0.0"
        settings.x402_enabled = False
        settings.ai_bettor_enabled = False

        app = create_app(settings, WSManager())
        client = TestClient(app)
        response = client.get("/api/blockchain-config")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["contract_address"] == "0x1234"
        assert data["chain_id"] == 10143
