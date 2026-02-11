"""Tests for Moltbook API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.moltbook.client import MoltbookClient


@pytest.mark.asyncio
class TestMoltbookClient:
    """Tests for MoltbookClient."""

    @pytest.fixture
    def mock_httpx_client(self):
        """Create mock httpx.AsyncClient."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.post = AsyncMock()
        mock.aclose = AsyncMock()
        return mock

    @pytest.fixture
    async def client(self, mock_httpx_client):
        """Create MoltbookClient with mocked httpx client."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MoltbookClient(base_url="https://api.moltbook.io", timeout=30.0)
            yield client
            await client.close()

    async def test_initialization(self):
        """Test client initialization."""
        client = MoltbookClient(base_url="https://api.moltbook.io", timeout=30.0)

        assert client.base_url == "https://api.moltbook.io"
        assert client.timeout == 30.0
        assert client.client is not None

        await client.close()

    async def test_initialization_strips_trailing_slash(self):
        """Test that base_url trailing slash is removed."""
        client = MoltbookClient(base_url="https://api.moltbook.io/", timeout=30.0)

        assert client.base_url == "https://api.moltbook.io"

        await client.close()

    async def test_validate_api_key_success(self, client, mock_httpx_client):
        """Test successful API key validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "agent-123",
            "name": "TestAgent",
            "status": "active",
        }

        mock_httpx_client.get.return_value = mock_response

        result = await client.validate_api_key("test-key")

        assert result is not None
        assert result["id"] == "agent-123"
        assert result["name"] == "TestAgent"

        mock_httpx_client.get.assert_called_once_with(
            "https://api.moltbook.io/api/agents/me",
            headers={"Authorization": "Bearer test-key"},
        )

    async def test_validate_api_key_invalid(self, client, mock_httpx_client):
        """Test API key validation with invalid key."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_httpx_client.get.return_value = mock_response

        result = await client.validate_api_key("invalid-key")

        assert result is None

    async def test_validate_api_key_http_error(self, client, mock_httpx_client):
        """Test API key validation with HTTP error."""
        mock_httpx_client.get.side_effect = httpx.RequestError("Network error")

        result = await client.validate_api_key("test-key")

        assert result is None

    async def test_send_dm_success(self, client, mock_httpx_client):
        """Test successful DM send."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_httpx_client.post.return_value = mock_response

        result = await client.send_dm(
            agent_id="agent-123",
            message="Hello, agent!",
            api_key="test-key",
        )

        assert result is True

        mock_httpx_client.post.assert_called_once_with(
            "https://api.moltbook.io/api/agents/agent-123/messages",
            headers={"Authorization": "Bearer test-key"},
            json={"message": "Hello, agent!"},
        )

    async def test_send_dm_created_status(self, client, mock_httpx_client):
        """Test DM send with 201 Created status."""
        mock_response = MagicMock()
        mock_response.status_code = 201

        mock_httpx_client.post.return_value = mock_response

        result = await client.send_dm(
            agent_id="agent-123",
            message="Hello!",
            api_key="test-key",
        )

        assert result is True

    async def test_send_dm_failure(self, client, mock_httpx_client):
        """Test DM send failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400

        mock_httpx_client.post.return_value = mock_response

        result = await client.send_dm(
            agent_id="agent-123",
            message="Hello!",
            api_key="test-key",
        )

        assert result is False

    async def test_send_dm_http_error(self, client, mock_httpx_client):
        """Test DM send with HTTP error."""
        mock_httpx_client.post.side_effect = httpx.RequestError("Network error")

        result = await client.send_dm(
            agent_id="agent-123",
            message="Hello!",
            api_key="test-key",
        )

        assert result is False

    async def test_poll_response_immediate_success(self, client, mock_httpx_client):
        """Test polling with immediate response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"id": "msg-1", "content": "This is my response"},
            ]
        }

        mock_httpx_client.get.return_value = mock_response

        result = await client.poll_response(
            agent_id="agent-123",
            since_id="msg-0",
            api_key="test-key",
            timeout=5.0,
        )

        assert result == "This is my response"

        mock_httpx_client.get.assert_called_once()
        call_args = mock_httpx_client.get.call_args
        assert call_args[1]["params"] == {"since": "msg-0"}

    async def test_poll_response_no_since_id(self, client, mock_httpx_client):
        """Test polling without since_id."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"id": "msg-1", "content": "Response"},
            ]
        }

        mock_httpx_client.get.return_value = mock_response

        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
            timeout=5.0,
        )

        assert result == "Response"

        call_args = mock_httpx_client.get.call_args
        assert call_args[1]["params"] == {}

    async def test_poll_response_timeout(self, client, mock_httpx_client):
        """Test polling timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": []}  # No messages

        mock_httpx_client.get.return_value = mock_response

        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
            timeout=3.0,  # Allow for at least 2 poll attempts (0s, 2s)
        )

        assert result is None
        # Should have tried multiple times (at least 2)
        assert mock_httpx_client.get.call_count >= 2

    async def test_poll_response_http_error_retry(self, client, mock_httpx_client):
        """Test polling with HTTP errors and retry."""
        # First call fails, second succeeds
        error_response = httpx.RequestError("Network error")
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "messages": [{"id": "msg-1", "content": "Success"}]
        }

        mock_httpx_client.get.side_effect = [error_response, success_response]

        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
            timeout=5.0,
        )

        assert result == "Success"
        assert mock_httpx_client.get.call_count == 2

    async def test_poll_response_empty_messages(self, client, mock_httpx_client):
        """Test polling with empty message list initially."""
        empty_response = MagicMock()
        empty_response.status_code = 200
        empty_response.json.return_value = {"messages": []}

        filled_response = MagicMock()
        filled_response.status_code = 200
        filled_response.json.return_value = {
            "messages": [{"id": "msg-1", "content": "Finally!"}]
        }

        mock_httpx_client.get.side_effect = [empty_response, filled_response]

        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
            timeout=5.0,
        )

        assert result == "Finally!"
        assert mock_httpx_client.get.call_count == 2

    async def test_poll_response_default_timeout(self, client, mock_httpx_client):
        """Test polling uses client default timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "msg-1", "content": "Response"}]
        }

        mock_httpx_client.get.return_value = mock_response

        # Don't pass timeout, should use client default (30.0)
        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
        )

        assert result == "Response"

    async def test_close(self, mock_httpx_client):
        """Test client close."""
        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            client = MoltbookClient(base_url="https://api.moltbook.io")
            await client.close()

        mock_httpx_client.aclose.assert_called_once()

    async def test_multiple_messages_returns_first(self, client, mock_httpx_client):
        """Test that poll_response returns first message when multiple exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"id": "msg-1", "content": "First message"},
                {"id": "msg-2", "content": "Second message"},
            ]
        }

        mock_httpx_client.get.return_value = mock_response

        result = await client.poll_response(
            agent_id="agent-123",
            since_id=None,
            api_key="test-key",
            timeout=5.0,
        )

        assert result == "First message"
