"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.ws_manager import WSManager
from src.config.settings import Settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def create_app(settings: Settings, ws_manager: WSManager, betting_manager=None) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        settings: Application settings.
        ws_manager: WebSocket manager instance.
        betting_manager: Optional betting manager for spectator betting.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="MafiaAI",
        description="AI agents play Mafia with real-time spectating",
        version="0.1.0",
    )

    # Store betting manager for WebSocket handler access
    app.state.betting_manager = betting_manager

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include REST API routes
    app.include_router(router)

    # Static files (will be created by p-impl-ui)
    static_dir = Path(__file__).parent.parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        log.info("static_files_mounted", path=str(static_dir))

        @app.get("/")
        async def index():
            """Serve index.html."""
            index_path = static_dir / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"message": "MafiaAI API - UI not yet available"}
    else:
        log.warning("static_dir_not_found", path=str(static_dir))

        @app.get("/")
        async def root():
            """Root endpoint when no static files."""
            return {
                "message": "MafiaAI API",
                "docs": "/docs",
                "health": "/api/health",
            }

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        """WebSocket endpoint for real-time game events.

        Args:
            ws: WebSocket connection.
        """
        await ws_manager.connect(ws)

        # Generate session ID for this connection
        import uuid

        session_id = str(uuid.uuid4())

        try:
            while True:
                data = await ws.receive_json()

                # Handle bet placement from client
                if data.get("type") == "place_bet":
                    log.info("bet_received", data=data)

                    if app.state.betting_manager:
                        bet_type = data.get("bet_type")
                        target = data.get("target")
                        amount = data.get("amount", 0)
                        round_number = data.get("round", 0)

                        bet = app.state.betting_manager.place_bet(
                            session_id, bet_type, target, amount, round_number
                        )

                        if bet:
                            balance = app.state.betting_manager.get_spectator_balance(
                                session_id
                            )
                            await ws.send_json(
                                {
                                    "type": "bet_confirmed",
                                    "data": {
                                        "bet_id": bet.bet_id,
                                        "bet_type": bet.bet_type.value,
                                        "target": bet.target,
                                        "amount": float(bet.amount),
                                        "weight": float(bet.weight),
                                        "new_balance": float(balance),
                                    },
                                }
                            )
                        else:
                            balance = app.state.betting_manager.get_spectator_balance(
                                session_id
                            )
                            await ws.send_json(
                                {
                                    "type": "bet_rejected",
                                    "data": {
                                        "reason": "Insufficient chips or invalid bet",
                                        "balance": float(balance),
                                    },
                                }
                            )
                    else:
                        await ws.send_json(
                            {
                                "type": "bet_rejected",
                                "data": {"reason": "Betting not enabled"},
                            }
                        )

                # Echo for debugging
                elif data.get("type") == "ping":
                    await ws.send_json({"type": "pong"})

        except WebSocketDisconnect:
            ws_manager.disconnect(ws)
            log.info("ws_client_disconnected")

        except Exception as exc:
            log.error("ws_error", error=str(exc))
            ws_manager.disconnect(ws)

    return app
