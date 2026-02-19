"""CLI entry point for MafiaAI game."""

import argparse
import asyncio
import time
from datetime import datetime

import uvicorn

from src.api.server import create_app
from src.api.ws_manager import WSManager
from src.cli.terminal import print_event, run_terminal_mode
from src.config.settings import load_settings
from src.models.events import WSEvent
from src.utils.logger import get_logger, setup_logging

log = get_logger(__name__)


async def run_server_mode(settings, ws_manager: WSManager) -> None:
    """Run game in server mode with FastAPI and WebSocket broadcasting.

    Args:
        settings: Application settings.
        ws_manager: WebSocket manager instance.
    """
    import uuid

    from src.agents.llm_client import LLMClient
    from src.agents.personalities import ALL_PERSONALITIES
    from src.betting.manager import BettingManager
    from src.lobby.manager import LobbyManager

    # Generate game_id upfront
    game_id = str(uuid.uuid4())

    # Create LLM client and betting manager
    llm_client = LLMClient(settings)
    betting_manager = BettingManager(llm_client, game_id)

    # Create AI spectator commentator if enabled
    commentator = None
    if settings.ai_spectator_enabled:
        from src.spectator.commentator import SpectatorCommentator
        commentator = SpectatorCommentator(llm_client)
        log.info("ai_spectator_commentator_enabled")

    # Create lobby manager
    lobby_manager = LobbyManager()

    # Initialize blockchain if enabled
    blockchain_gateway = None
    if settings.blockchain_enabled:
        try:
            from src.blockchain.gateway import BlockchainGateway
            from src.blockchain.provider import BlockchainProvider

            import os
            pk = settings.blockchain_private_key.get_secret_value()
            if not pk:
                pk = os.environ.get("BLOCKCHAIN_PRIVATE_KEY", "")
            if not pk:
                log.warning("blockchain_private_key_missing", msg="BLOCKCHAIN_ENABLED=true but no private key set")
            else:
                provider = BlockchainProvider(
                    rpc_url=settings.blockchain_rpc_url,
                    private_key=pk,
                    contract_address=settings.blockchain_contract_address,
                )
                if await provider.is_connected():
                    blockchain_gateway = BlockchainGateway(provider, settings.blockchain_token_decimals)
                    log.info("blockchain_connected", rpc=settings.blockchain_rpc_url, chain_id=settings.blockchain_chain_id)
                else:
                    log.warning("blockchain_connection_failed")
        except Exception as exc:
            log.warning("blockchain_init_failed", error=str(exc))

    # Create FastAPI app with betting manager
    app = create_app(settings, ws_manager, betting_manager)

    # Store lobby manager on app state
    app.state.lobby_manager = lobby_manager

    # Start AI bettor if enabled
    bettor_task = None
    if settings.ai_bettor_enabled:
        try:
            from decimal import Decimal

            from src.ai_bettor.client import AIBettorClient

            bettor = AIBettorClient(
                ws_url=f"ws://localhost:{settings.port}/ws",
                api_url=f"http://localhost:{settings.port}",
                api_key=settings.openai_api_key.get_secret_value(),
                budget_usdc=Decimal(str(settings.ai_bettor_budget_usdc)),
                private_key=settings.ai_bettor_private_key.get_secret_value() or None,
            )
            bettor_task = asyncio.create_task(bettor.run())
            log.info("ai_bettor_started", budget=settings.ai_bettor_budget_usdc)
        except ImportError:
            log.warning("ai_bettor_not_available", reason="module_not_found")

    # Configure uvicorn server
    config = uvicorn.Config(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)

    print("\n" + "="*60)
    print("MafiaAI - Server Mode")
    print("="*60)
    print(f"Server: http://{settings.host}:{settings.port}")
    print(f"API Docs: http://localhost:{settings.port}/docs")
    print(f"WebSocket: ws://localhost:{settings.port}/ws")
    print("="*60 + "\n")

    # Broadcast wrapper that also feeds AI commentator
    async def broadcast_spec_chat(name: str, text: str, is_ai: bool) -> None:
        """Broadcast a spectator chat message to all clients."""
        await ws_manager.broadcast(
            WSEvent(
                event_type="spec_chat_message",
                data={"name": name, "text": text, "isAi": is_ai},
                game_id="",
                timestamp=datetime.now().isoformat(),
            )
        )

    async def broadcast_with_commentary(event: WSEvent) -> None:
        """Broadcast game event and trigger AI commentary."""
        await ws_manager.broadcast(event)
        if commentator is not None:
            asyncio.create_task(
                commentator.on_game_event(
                    event.event_type,
                    event.data,
                    broadcast_spec_chat,
                )
            )

    from src.engine.game_engine import GameEngine

    # Continuous game loop
    async def game_loop():
        """Continuous game loop: lobby → game → reset → lobby."""
        while True:
            lobby_timeout_seconds = getattr(settings, "lobby_timeout_seconds", 30)
            log.info("lobby_waiting", timeout=lobby_timeout_seconds)
            print(f"[...] Lobby waiting for players ({lobby_timeout_seconds}s timeout)...")

            # Wait for first player to join
            while lobby_manager.first_join_time is None:
                await asyncio.sleep(1)

            # Wait for remaining lobby timeout from first join
            elapsed = time.time() - lobby_manager.first_join_time
            remaining = max(0, lobby_timeout_seconds - elapsed)
            if remaining > 0:
                await asyncio.sleep(remaining)

            # Fill remaining slots with House AI
            log.info("filling_with_house_ai")
            lobby_manager.fill_with_house_ai(llm_client, ALL_PERSONALITIES)
            players = lobby_manager.get_players()

            # Generate new game_id for this round
            import uuid
            round_game_id = str(uuid.uuid4())

            # Broadcast updated lobby status
            await ws_manager.broadcast(
                WSEvent(
                    event_type="lobby_status",
                    data=lobby_manager.get_lobby_status(),
                    game_id=round_game_id,
                    timestamp=datetime.now().isoformat(),
                )
            )

            log.info("game_starting", player_count=len(players))
            print(f"\n[>] Starting game with {len(players)} players...")

            # Create engine — use commentary wrapper if AI spectator enabled
            engine = GameEngine(
                players,
                broadcast_with_commentary,
                betting_manager,
                round_game_id,
                blockchain_gateway,
            )

            # Broadcast game starting
            await ws_manager.broadcast(
                WSEvent(
                    event_type="game_starting",
                    data={
                        "player_count": len(players),
                        "players": [
                            {"name": p.name, "player_type": p.player_type.value}
                            for p in players.values()
                        ],
                    },
                    game_id=round_game_id,
                    timestamp=datetime.now().isoformat(),
                )
            )

            app.state.game_active = True

            try:
                final_state = await engine.run_game()
                app.state.current_game = final_state
                log.info("game_completed", winner=final_state.winner)
                print(f"\n[OK] Game completed! Winner: {final_state.winner}")
            except Exception as exc:
                log.exception("game_error", error=str(exc))
            finally:
                app.state.game_active = False

            # Cooldown before new lobby
            print("[...] New lobby opening in 10 seconds...")
            await asyncio.sleep(10)

            # Reset for next game
            lobby_manager.reset()
            ws_manager.clear_sessions()
            betting_manager.reset(str(uuid.uuid4()))

            # Broadcast new_lobby event
            await ws_manager.broadcast(
                WSEvent(
                    event_type="new_lobby",
                    data={"message": "New game lobby is open!"},
                    game_id="",
                    timestamp=datetime.now().isoformat(),
                )
            )

    game_task = asyncio.create_task(game_loop())

    try:
        # Run server (blocks until shutdown)
        await server.serve()

        # Wait for game to complete
        await game_task

    except asyncio.CancelledError:
        log.info("server_shutdown")
        game_task.cancel()
        try:
            await game_task
        except asyncio.CancelledError:
            pass

        # Cancel AI bettor if running
        if bettor_task:
            bettor_task.cancel()
            try:
                await bettor_task
            except asyncio.CancelledError:
                pass


async def main() -> None:
    """Run MafiaAI in server or terminal mode."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="MafiaAI - AI agents play Mafia")
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Terminal-only mode (no web server)",
    )
    args = parser.parse_args()

    # Load settings
    settings = load_settings()

    # Setup logging
    setup_logging(settings.log_level)

    log.info("starting_mafia_ai", mode="terminal" if args.no_api else "server")

    # Verify API key
    if not settings.openai_api_key.get_secret_value():
        log.error("openai_api_key_missing")
        print("\n[ERR] Error: OPENAI_API_KEY not set in environment or .env file")
        print("Please set your API key and try again.\n")
        return

    # Run in selected mode
    if args.no_api:
        await run_terminal_mode(settings)
    else:
        ws_manager = WSManager()
        await run_server_mode(settings, ws_manager)


if __name__ == "__main__":
    asyncio.run(main())
