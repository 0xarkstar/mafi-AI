"""REST API routes."""

from fastapi import APIRouter, HTTPException

from src.models.game import GameState
from src.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/api")

# Global state (will be set by server.py)
_current_game: GameState | None = None
_game_active: bool = False


def set_game_state(state: GameState | None) -> None:
    """Update the current game state (called by game engine).

    Args:
        state: Current game state or None if no game running.
    """
    global _current_game
    _current_game = state


def set_game_active(active: bool) -> None:
    """Update game active status.

    Args:
        active: True if game is running, False otherwise.
    """
    global _game_active
    _game_active = active


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status and game activity.
    """
    return {
        "status": "ok",
        "game_active": _game_active,
        "game_id": _current_game.game_id if _current_game else None,
    }


@router.get("/games/{game_id}")
async def get_game(game_id: str) -> dict:
    """Get current game state.

    Args:
        game_id: Game ID to retrieve.

    Returns:
        Current game state as JSON.

    Raises:
        HTTPException: If game not found or not active.
    """
    if not _current_game:
        raise HTTPException(status_code=404, detail="No active game")

    if _current_game.game_id != game_id:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    return _current_game.model_dump()
