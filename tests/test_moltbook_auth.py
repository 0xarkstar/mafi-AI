"""Tests for Moltbook Identity authentication."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from src.moltbook.auth import MoltbookAuth


class TestMoltbookAuth:
    """Tests for MoltbookAuth.verify_identity()."""

    @pytest.mark.asyncio
    async def test_verify_identity_success(self):
        """Test successful identity verification."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "agent": {
                "id": "agent-123",
                "name": "TestAgent",
                "wallet_address": "0x1234567890abcdef",
            },
        }

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        # Call verify_identity
        agent_info = await auth.verify_identity("valid-token-123")

        # Verify result
        assert agent_info["id"] == "agent-123"
        assert agent_info["name"] == "TestAgent"
        assert agent_info["wallet_address"] == "0x1234567890abcdef"

        # Verify POST request made correctly
        auth.http_client.post.assert_called_once_with(
            "https://moltbook.com/api/v1/agents/verify-identity",
            headers={"X-Moltbook-App-Key": "moltdev_test"},
            json={"token": "valid-token-123", "audience": "mafia-ai.test"},
        )

    @pytest.mark.asyncio
    async def test_verify_identity_expired_token(self):
        """Test verification fails with expired token."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock 401 response with expired token error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "identity_token_expired"}'
        mock_response.json.return_value = {"error": "identity_token_expired"}

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        # Verify raises HTTPException 401
        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("expired-token")

        assert exc_info.value.status_code == 401
        assert "identity_token_expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_invalid_token(self):
        """Test verification fails with invalid token."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock 401 response with invalid token
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "invalid_token"}'
        mock_response.json.return_value = {"error": "invalid_token"}

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("bad-token")

        assert exc_info.value.status_code == 401
        assert "invalid_token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_agent_not_found(self):
        """Test verification fails with agent_not_found error."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "agent_not_found"}'
        mock_response.json.return_value = {"error": "agent_not_found"}

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("unknown-agent-token")

        assert exc_info.value.status_code == 401
        assert "agent_not_found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_audience_mismatch(self):
        """Test verification fails with audience_mismatch error."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock 401 response with audience mismatch
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error": "audience_mismatch"}'
        mock_response.json.return_value = {"error": "audience_mismatch"}

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("wrong-audience-token")

        assert exc_info.value.status_code == 401
        assert "audience_mismatch" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_valid_false(self):
        """Test verification fails when valid=false in response."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock 200 response but valid=false
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"valid": False}

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("invalid-token")

        assert exc_info.value.status_code == 401
        assert "Invalid identity token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_missing_fields(self):
        """Test verification fails when required fields missing in response."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock response missing wallet_address
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "valid": True,
            "agent": {
                "id": "agent-123",
                "name": "TestAgent",
                # Missing wallet_address
            },
        }

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("token")

        assert exc_info.value.status_code == 401
        assert "Incomplete agent information" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_network_error(self):
        """Test verification fails with network error."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock network error
        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("token")

        assert exc_info.value.status_code == 503
        assert "Moltbook service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_identity_timeout(self):
        """Test verification fails with timeout."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock timeout error
        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("token")

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_verify_identity_empty_response(self):
        """Test verification handles empty response body."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        # Mock response with no text
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = ""

        auth.http_client = MagicMock()
        auth.http_client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await auth.verify_identity("token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_close_http_client(self):
        """Test that close() closes the HTTP client."""
        auth = MoltbookAuth(
            app_key="moltdev_test",
            audience="mafia-ai.test",
            moltbook_api_url="https://moltbook.com/api",
        )

        auth.http_client = MagicMock()
        auth.http_client.aclose = AsyncMock()

        await auth.close()

        auth.http_client.aclose.assert_called_once()
