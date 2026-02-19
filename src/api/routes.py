"""REST API routes."""

from fastapi import APIRouter, HTTPException, Request

from src.utils.logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint."""
    current_game = getattr(request.app.state, "current_game", None)
    return {
        "status": "ok",
        "game_active": getattr(request.app.state, "game_active", False),
        "game_id": current_game.game_id if current_game else None,
    }


@router.get("/games/{game_id}")
async def get_game(game_id: str, request: Request) -> dict:
    """Get current game state."""
    current_game = getattr(request.app.state, "current_game", None)
    if not current_game:
        raise HTTPException(status_code=404, detail="No active game")

    if current_game.game_id != game_id:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    return current_game.model_dump()


@router.get("/odds")
async def get_odds(request: Request) -> dict:
    """Get current betting odds."""
    betting_manager = getattr(request.app.state, "betting_manager", None)
    if betting_manager and betting_manager.odds_board:
        odds = betting_manager.odds_board
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


@router.get("/blockchain-config")
async def blockchain_config(request: Request) -> dict:
    """Return blockchain configuration for frontend."""
    s = request.app.state.settings
    return {
        "enabled": s.blockchain_enabled,
        "contract_address": s.blockchain_contract_address if s.blockchain_enabled else "",
        "chain_id": s.blockchain_chain_id if s.blockchain_enabled else 0,
        "rpc_url": s.blockchain_rpc_url if s.blockchain_enabled else "",
    }
