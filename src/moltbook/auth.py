"""Moltbook Identity authentication."""

import httpx
import structlog
from fastapi import HTTPException, status

logger = structlog.get_logger(__name__)


class MoltbookAuth:
    """Handles Moltbook Identity token verification."""

    def __init__(self, app_key: str, audience: str, moltbook_api_url: str):
        """Initialize Moltbook auth.

        Args:
            app_key: Moltbook app key (moltdev_xxx).
            audience: Audience restriction (e.g., "mafia-ai.example.com").
            moltbook_api_url: Base URL for Moltbook API.
        """
        self.app_key = app_key
        self.audience = audience
        self.verify_url = f"{moltbook_api_url}/v1/agents/verify-identity"
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def verify_identity(self, identity_token: str) -> dict:
        """Verify Moltbook identity token.

        Makes POST request to Moltbook verification endpoint:
        POST https://moltbook.com/api/v1/agents/verify-identity
        Headers: X-Moltbook-App-Key: {app_key}
        Body: {"token": identity_token, "audience": self.audience}

        Args:
            identity_token: JWT identity token from agent.

        Returns:
            Agent info dict with keys: id, name, wallet_address

        Raises:
            HTTPException: 401 if verification fails.
                Error codes: identity_token_expired, invalid_token,
                            agent_not_found, audience_mismatch
        """
        try:
            response = await self.http_client.post(
                self.verify_url,
                headers={"X-Moltbook-App-Key": self.app_key},
                json={"token": identity_token, "audience": self.audience},
            )

            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_code = error_data.get("error", "verification_failed")
                logger.warning(
                    "moltbook_verification_failed",
                    status=response.status_code,
                    error=error_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Moltbook verification failed: {error_code}",
                )

            data = response.json()

            if not data.get("valid"):
                logger.warning("moltbook_token_invalid", data=data)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid identity token",
                )

            agent_info = data.get("agent", {})

            # Verify required fields
            if not all(key in agent_info for key in ["id", "name", "wallet_address"]):
                logger.error("moltbook_missing_fields", agent_info=agent_info)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incomplete agent information",
                )

            logger.info(
                "moltbook_verification_success",
                agent_id=agent_info["id"],
                agent_name=agent_info["name"],
            )

            return agent_info

        except httpx.RequestError as exc:
            logger.error("moltbook_request_error", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Moltbook service unavailable",
            ) from exc

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
