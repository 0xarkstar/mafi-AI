"""FastAPI application factory."""

from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.ws_manager import WSManager
from src.config.settings import Settings
from src.models.events import WSEvent
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
    app.state.settings = settings

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
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

    # Include REST API routes
    app.include_router(router)

    # Blockchain configuration endpoint
    @app.get("/api/blockchain-config")
    async def blockchain_config():
        """Return blockchain configuration for frontend."""
        s = app.state.settings
        return {
            "enabled": s.blockchain_enabled,
            "contract_address": s.blockchain_contract_address if s.blockchain_enabled else "",
            "chain_id": s.blockchain_chain_id if s.blockchain_enabled else 0,
            "rpc_url": s.blockchain_rpc_url if s.blockchain_enabled else "",
        }

    # X402 betting endpoint
    @app.post("/api/bets/x402")
    async def place_x402_bet(request: Request):
        """Place a bet via X402 payment protocol.

        Any X402-compatible client (Moltbook agents, spectator agents,
        House AI bettor) can call this endpoint.
        """
        from decimal import Decimal as D

        try:
            # Parse request body
            body = await request.json()
            bet_type = body.get("bet_type")
            target = body.get("target")
            amount_usdc = body.get("amount_usdc", 0)
            round_number = body.get("round", 0)

            # Extract payment info from request state (injected by x402 middleware)
            # If x402_enabled=False, use a mock/test payment from headers
            if app.state.settings.x402_enabled:
                payment_info = getattr(request.state, "x402_payment", None)
                if not payment_info:
                    return {
                        "success": False,
                        "error": "X402 payment info missing",
                    }
                bettor_address = payment_info.payer_address
                tx_hash = payment_info.tx_hash
            else:
                # Test mode: accept any bet with mock payment
                bettor_address = request.headers.get("X-Test-Address", "test-address")
                tx_hash = request.headers.get("X-Test-TxHash", "test-tx-hash")

            # Validate betting manager exists
            if not app.state.betting_manager:
                return {
                    "success": False,
                    "error": "Betting not enabled",
                }

            # Place bet via X402 handler
            bet = app.state.betting_manager.handle_x402_bet(
                bettor_address=bettor_address,
                bet_type=bet_type,
                target=target,
                amount_usdc=D(str(amount_usdc)),
                round_number=round_number,
                tx_hash=tx_hash,
            )

            if not bet:
                return {
                    "success": False,
                    "error": "Invalid bet",
                }

            # Return confirmation with current odds
            odds_board = app.state.betting_manager.odds_board
            return {
                "success": True,
                "bet_id": bet.bet_id,
                "bet_type": bet.bet_type.value,
                "target": bet.target,
                "amount": float(bet.amount),
                "weight": float(bet.weight),
                "tx_hash": bet.tx_hash,
                "odds": {
                    "mafia_win": float(odds_board.mafia_win_prob)
                    if odds_board
                    else 0.5,
                    "citizen_win": float(odds_board.citizen_win_prob)
                    if odds_board
                    else 0.5,
                }
                if odds_board
                else {},
            }

        except Exception as exc:
            log.error("x402_bet_error", error=str(exc))
            return {
                "success": False,
                "error": str(exc),
            }

    # Moltbook agent join endpoint
    @app.post("/api/lobby/join-agent")
    async def join_agent(request_data: dict):
        """Moltbook agent joins the lobby.

        Args:
            request_data: Request body with api_key.

        Returns:
            Success/failure response.
        """
        api_key = request_data.get("api_key", "")

        if not api_key:
            return {"success": False, "error": "API key required"}

        # Check if lobby exists
        if not hasattr(app.state, "lobby_manager") or not app.state.lobby_manager:
            return {"success": False, "error": "Lobby not available"}

        try:
            # TODO: Validate with Moltbook API
            # For now, accept any non-empty key
            from src.moltbook.client import MoltbookClient
            from src.players.moltbook_agent import MoltbookAgentPlayer

            agent_name = f"Moltbook-{api_key[:6]}"
            moltbook_client = MoltbookClient(
                base_url=app.state.settings.moltbook_api_url
            )
            player = MoltbookAgentPlayer(
                name=agent_name,
                moltbook_client=moltbook_client,
                agent_id=api_key[:12],
                api_key=api_key,
            )
            success = await app.state.lobby_manager.join(player)

            if success:
                # Broadcast lobby status
                from datetime import datetime

                await ws_manager.broadcast(
                    WSEvent(
                        event_type="lobby_status",
                        data={
                            "players": list(app.state.lobby_manager.players.keys()),
                            "count": len(app.state.lobby_manager.players),
                            "ready": app.state.lobby_manager.is_ready(),
                        },
                        game_id="",
                        timestamp=datetime.now().isoformat(),
                    )
                )

            return {
                "success": success,
                "agent_name": agent_name if success else None,
                "players": list(app.state.lobby_manager.players.keys()),
            }

        except Exception as exc:
            log.error("moltbook_join_failed", error=str(exc))
            return {"success": False, "error": str(exc)}

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
        from datetime import datetime

        session_id = str(uuid.uuid4())

        try:
            while True:
                data = await ws.receive_json()

                # Join lobby as human player
                if data.get("type") == "join_lobby":
                    player_name = data.get("name", f"Human-{session_id[:6]}")

                    # Register this WS as a player
                    await ws_manager.register_player(player_name, ws)

                    # Create HumanPlayer and add to lobby
                    if hasattr(app.state, "lobby_manager") and app.state.lobby_manager:
                        from src.players.human import HumanPlayer

                        player = HumanPlayer(name=player_name, ws_manager=ws_manager)
                        success = await app.state.lobby_manager.join(player)

                        await ws.send_json(
                            {
                                "type": "lobby_joined",
                                "data": {
                                    "name": player_name,
                                    "success": success,
                                    "players": list(
                                        app.state.lobby_manager.players.keys()
                                    ),
                                },
                            }
                        )

                        # Broadcast lobby status to all
                        await ws_manager.broadcast(
                            WSEvent(
                                event_type="lobby_status",
                                data={
                                    "players": list(
                                        app.state.lobby_manager.players.keys()
                                    ),
                                    "count": len(app.state.lobby_manager.players),
                                    "ready": app.state.lobby_manager.is_ready(),
                                },
                                game_id="",
                                timestamp=datetime.now().isoformat(),
                            )
                        )
                    else:
                        await ws.send_json(
                            {
                                "type": "lobby_joined",
                                "data": {
                                    "name": player_name,
                                    "success": False,
                                    "players": [],
                                },
                            }
                        )

                # Human action response
                elif data.get("type") == "action_response":
                    player_name = data.get("player_name")
                    response = data.get("response", "")
                    ws_manager.resolve_response(player_name, response)

                # Handle bet placement from client
                elif data.get("type") == "place_bet":
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
