"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.bet_routes import router as bet_router
from src.api.lobby_routes import router as lobby_router
from src.api.routes import router
from src.api.ws_handler import websocket_endpoint
from src.api.ws_manager import WSManager
from src.config.settings import Settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def create_app(settings: Settings, ws_manager: WSManager, betting_manager=None) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="MafiaAI",
        description="AI agents play Mafia with real-time spectating",
        version="0.1.0",
    )

    # Store shared state
    app.state.betting_manager = betting_manager
    app.state.settings = settings
    app.state.ws_manager = ws_manager

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # X402 middleware (conditional)
    if settings.x402_enabled:
        try:
            from src.x402.middleware import create_x402_middleware

            x402_mw = create_x402_middleware(settings)
            app.add_middleware(x402_mw)
            log.info("x402_middleware_enabled")
        except ImportError:
            log.warning("x402_middleware_not_available", reason="module_not_found")

    # Include REST API routers
    app.include_router(router)
    app.include_router(bet_router)
    app.include_router(lobby_router)

    # WebSocket endpoint
    app.websocket("/ws")(websocket_endpoint)

    # Static files — mount /assets for Vite bundles
    static_dir = Path(__file__).parent.parent.parent / "static"
    assets_dir = static_dir / "assets"
    if static_dir.exists() and assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        log.info("static_files_mounted", path=str(static_dir))

    # Image assets from frontend
    images_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "images"
    if images_dir.exists():
        app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
        log.info("images_mounted", path=str(images_dir))

        @app.get("/")
        async def index():
            """Serve the SPA index.html."""
            return FileResponse(static_dir / "index.html")
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

    return app
