"""Lobby REST API routes for agent/player joining."""

from datetime import datetime

from fastapi import APIRouter, Request

from src.api.validators import validate_player_name
from src.models.events import WSEvent
from src.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter()


@router.post("/api/lobby/join-agent")
async def join_agent(request: Request):
    """Moltbook agent joins the lobby via Identity verification.

    Requires X-Moltbook-Identity header with JWT token.
    """
    if not hasattr(request.app.state, "lobby_manager") or not request.app.state.lobby_manager:
        return {"success": False, "error": "Lobby not available"}

    try:
        identity_token = request.headers.get("X-Moltbook-Identity", "")
        if not identity_token:
            return {"success": False, "error": "Moltbook Identity token required"}

        from src.moltbook.auth import MoltbookAuth

        auth = MoltbookAuth(
            app_key=request.app.state.settings.moltbook_app_key.get_secret_value(),
            audience=request.app.state.settings.moltbook_audience,
            moltbook_api_url=request.app.state.settings.moltbook_api_url,
        )
        agent_info = await auth.verify_identity(identity_token)

        agent_id = agent_info["id"]
        agent_name = agent_info["name"]
        wallet_address = agent_info["wallet_address"]

        from src.moltbook.client import MoltbookClient
        from src.players.moltbook_agent import MoltbookAgentPlayer

        moltbook_client = MoltbookClient(
            base_url=request.app.state.settings.moltbook_api_url
        )
        player = MoltbookAgentPlayer(
            name=agent_name,
            moltbook_client=moltbook_client,
            agent_id=agent_id,
            api_key="",
            wallet_address=wallet_address,
        )

        success = request.app.state.lobby_manager.join(player)

        if success:
            await request.app.state.ws_manager.broadcast(
                WSEvent(
                    event_type="lobby_status",
                    data=request.app.state.lobby_manager.get_lobby_status(),
                    game_id="",
                    timestamp=datetime.now().isoformat(),
                )
            )

        return {
            "success": success,
            "agent_name": agent_name if success else None,
            "wallet_address": wallet_address if success else None,
            "players": list(request.app.state.lobby_manager.players.keys()),
        }

    except ValueError as exc:
        log.warning("moltbook_join_validation_error", error=str(exc))
        return {"success": False, "error": f"Invalid request: {exc}"}
    except Exception as exc:
        log.error("moltbook_join_failed", error=str(exc))
        return {"success": False, "error": "Internal server error"}


@router.post("/api/lobby/join-moltbook")
async def join_moltbook(request: Request):
    """Moltbook agent joins the lobby by name and agent ID.

    Accepts JSON body: {"name": str, "moltbook_agent_id": str}
    """
    if not hasattr(request.app.state, "lobby_manager") or not request.app.state.lobby_manager:
        return {"success": False, "error": "Lobby not available"}

    try:
        body = await request.json()
        name = body.get("name", "")
        moltbook_agent_id = body.get("moltbook_agent_id", "")

        name_error = validate_player_name(name)
        if name_error:
            return {"success": False, "error": f"Invalid name: {name_error}"}

        if not moltbook_agent_id or not isinstance(moltbook_agent_id, str):
            return {"success": False, "error": "moltbook_agent_id must be a non-empty string"}

        from src.moltbook.client import MoltbookClient
        from src.players.moltbook_agent import MoltbookAgentPlayer

        moltbook_client = MoltbookClient(
            base_url=request.app.state.settings.moltbook_api_url
        )
        player = MoltbookAgentPlayer(
            name=name,
            agent_id=moltbook_agent_id,
            api_key="",
            moltbook_client=moltbook_client,
        )

        success = request.app.state.lobby_manager.join(player)

        if success:
            await request.app.state.ws_manager.broadcast(
                WSEvent(
                    event_type="lobby_status",
                    data=request.app.state.lobby_manager.get_lobby_status(),
                    game_id="",
                    timestamp=datetime.now().isoformat(),
                )
            )

        return {
            "success": success,
            "message": "Agent joined lobby" if success else "Lobby full",
        }

    except ValueError as exc:
        log.warning("moltbook_join_validation_error", error=str(exc))
        return {"success": False, "error": f"Invalid request: {exc}"}
    except Exception as exc:
        log.error("moltbook_join_failed", error=str(exc))
        return {"success": False, "error": "Internal server error"}
