"""Moltbook API client for external agent communication."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import httpx

from src.utils.logger import get_logger

log = get_logger(__name__)


class MoltbookClient:
    """Client for interacting with Moltbook external agent API."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        """Initialize Moltbook client.

        Args:
            base_url: Base URL for Moltbook API.
            timeout: Default timeout for requests.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def validate_api_key(self, api_key: str) -> dict | None:
        """Validate API key and get agent info.

        Args:
            api_key: Bearer token for authentication.

        Returns:
            Agent info dict on success, None on failure.
        """
        log.info("validating_moltbook_api_key")

        try:
            response = await self.client.get(
                f"{self.base_url}/api/agents/me",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                log.info("moltbook_api_key_valid", agent_id=data.get("id"))
                return data

            log.warning("moltbook_api_key_invalid", status_code=response.status_code)
            return None

        except httpx.HTTPError as e:
            log.error("moltbook_validation_error", error=str(e))
            return None

    async def send_dm(self, agent_id: str, message: str, api_key: str) -> bool:
        """Send direct message to agent.

        Args:
            agent_id: Target agent ID.
            message: Message content.
            api_key: Bearer token for authentication.

        Returns:
            True on success, False on failure.
        """
        log.info("sending_moltbook_dm", agent_id=agent_id, length=len(message))

        try:
            response = await self.client.post(
                f"{self.base_url}/api/agents/{agent_id}/messages",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"message": message},
            )

            if response.status_code in (200, 201):
                log.info("moltbook_dm_sent", agent_id=agent_id)
                return True

            log.warning(
                "moltbook_dm_failed",
                agent_id=agent_id,
                status_code=response.status_code,
            )
            return False

        except httpx.HTTPError as e:
            log.error("moltbook_dm_error", agent_id=agent_id, error=str(e))
            return False

    async def poll_response(
        self,
        agent_id: str,
        since_id: str | None,
        api_key: str,
        timeout: float | None = None,
    ) -> str | None:
        """Poll for agent response messages.

        Args:
            agent_id: Target agent ID.
            since_id: Last message ID seen (for filtering).
            api_key: Bearer token for authentication.
            timeout: Polling timeout in seconds.

        Returns:
            Response message text or None on timeout/error.
        """
        timeout = timeout or self.timeout
        deadline = datetime.now() + timedelta(seconds=timeout)

        log.info("polling_moltbook_response", agent_id=agent_id, timeout=timeout)

        while datetime.now() < deadline:
            try:
                params = {"since": since_id} if since_id else {}

                response = await self.client.get(
                    f"{self.base_url}/api/agents/{agent_id}/messages",
                    headers={"Authorization": f"Bearer {api_key}"},
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    messages = data.get("messages", [])

                    # Return first new message
                    if messages:
                        message_text = messages[0].get("content", "")
                        log.info(
                            "moltbook_response_received",
                            agent_id=agent_id,
                            length=len(message_text),
                        )
                        return message_text

                # Poll every 2 seconds
                await asyncio.sleep(2)

            except httpx.HTTPError as e:
                log.error("moltbook_poll_error", agent_id=agent_id, error=str(e))
                await asyncio.sleep(2)

        log.warning("moltbook_poll_timeout", agent_id=agent_id)
        return None
