"""REST API routes."""

import asyncio

from fastapi import APIRouter, HTTPException

from src.models.game import GameState
from src.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/api")

# Global state (will be set by server.py)
_current_game: GameState | None = None
_game_active: bool = False
_betting_manager = None
_state_lock = asyncio.Lock()


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


def set_betting_manager(manager) -> None:
    """Update betting manager reference.

    Args:
        manager: BettingManager instance or None.
    """
    global _betting_manager
    _betting_manager = manager


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


@router.get("/odds")
async def get_odds() -> dict:
    """Get current betting odds.

    Returns:
        Current odds board as JSON.
    """
    if _betting_manager and _betting_manager.odds_board:
        odds = _betting_manager.odds_board
        return {
            "game_id": odds.game_id,
            "round_number": odds.round_number,
            "mafia_win_prob": float(odds.mafia_win_prob),
            "citizen_win_prob": float(odds.citizen_win_prob),
            "mafia_suspects": {
                name: float(prob) for name, prob in odds.mafia_suspects.items()
            },
        }
    return {"message": "No odds available"}
