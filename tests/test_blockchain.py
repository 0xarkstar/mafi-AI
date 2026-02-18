"""Tests for blockchain integration module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.blockchain.provider import BlockchainProvider, create_web3_provider


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


class TestCreateWeb3Provider:
    """Tests for create_web3_provider factory function."""

    @pytest.mark.asyncio
    async def test_create_web3_provider_success(self):
        """Test successful provider creation with POA middleware injected."""
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3_cls, \
             patch("src.blockchain.provider.AsyncHTTPProvider") as mock_provider_cls, \
             patch("src.blockchain.provider.ExtraDataToPOAMiddleware"):
            mock_instance = MagicMock()
            mock_instance.middleware_onion = MagicMock()
            mock_instance.is_connected = AsyncMock(return_value=True)
            mock_web3_cls.return_value = mock_instance

            result = await create_web3_provider("https://testnet-rpc.monad.xyz", 10143)

            assert result is mock_instance
            mock_instance.middleware_onion.inject.assert_called_once()
            mock_instance.is_connected.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_web3_provider_connection_failure(self):
        """Test ConnectionError raised when RPC not reachable."""
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3_cls, \
             patch("src.blockchain.provider.AsyncHTTPProvider"), \
             patch("src.blockchain.provider.ExtraDataToPOAMiddleware"):
            mock_instance = MagicMock()
            mock_instance.middleware_onion = MagicMock()
            mock_instance.is_connected = AsyncMock(return_value=False)
            mock_web3_cls.return_value = mock_instance

            with pytest.raises(ConnectionError, match="Cannot connect"):
                await create_web3_provider("https://bad-rpc.example.com", 10143)


class TestBlockchainProviderGetContract:
    """Tests for BlockchainProvider.get_contract versioning."""

    def _make_provider(self):
        with patch("src.blockchain.provider.AsyncWeb3") as mock_web3_cls, \
             patch("src.blockchain.provider.ExtraDataToPOAMiddleware"):
            instance = MagicMock()
            instance.middleware_onion = MagicMock()
            instance.eth = MagicMock()
            instance.eth.account = MagicMock()
            instance.eth.account.from_key = MagicMock(return_value=MagicMock())
            instance.eth.contract = MagicMock(return_value=MagicMock())
            instance.to_checksum_address = MagicMock(return_value="0x" + "b" * 40)
            mock_web3_cls.return_value = instance
            return BlockchainProvider(
                rpc_url="https://rpc",
                private_key="0x" + "a" * 64,
                contract_address="0x" + "b" * 40,
            ), instance

    @pytest.mark.asyncio
    async def test_get_contract_v1_default(self):
        """Test default version loads V1 ABI path."""
        import json
        provider, w3_instance = self._make_provider()

        v1_abi = {"abi": []}
        with patch("builtins.open", MagicMock()) as mock_open, \
             patch("json.load", return_value=v1_abi):
            contract = await provider.get_contract()

        w3_instance.eth.contract.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contract_v2(self):
        """Test version='v2' loads V2 ABI path."""
        import json
        provider, w3_instance = self._make_provider()

        v2_abi = {"abi": []}
        with patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=v2_abi):
            contract_v2 = await provider.get_contract(version="v2")

        w3_instance.eth.contract.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_contract_caching(self):
        """Test that same version returns cached contract."""
        import json
        provider, w3_instance = self._make_provider()

        v1_abi = {"abi": []}
        with patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=v1_abi):
            contract1 = await provider.get_contract(version="v1")
            contract2 = await provider.get_contract(version="v1")

        # open() should only be called once (caching)
        assert contract1 is contract2
        assert w3_instance.eth.contract.call_count == 1


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
