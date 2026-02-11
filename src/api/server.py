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


def create_app(settings: Settings, ws_manager: WSManager) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        settings: Application settings.
        ws_manager: WebSocket manager instance.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="MafiaAI",
        description="AI agents play Mafia with real-time spectating",
        version="0.1.0",
    )

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
        try:
            while True:
                data = await ws.receive_json()

                # Handle bet placement from client (Day 3 feature)
                if data.get("type") == "place_bet":
                    log.info("bet_received", data=data)
                    # TODO: Day 3 betting integration
                    # Will forward to betting module when implemented
                    pass

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
