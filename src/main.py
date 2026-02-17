"""CLI entry point for MafiaAI game."""

import argparse
import asyncio

import uvicorn

from src.api.routes import set_betting_manager, set_game_active, set_game_state
from src.api.server import create_app
from src.api.ws_manager import WSManager
from src.config.settings import load_settings
from src.engine.game_engine import GameEngine
from src.models.events import WSEvent
from src.utils.logger import get_logger, setup_logging

log = get_logger(__name__)


async def print_event(event: WSEvent) -> None:
    """Simple event callback that prints to terminal.

    Args:
        event: WebSocket event to print.
    """
    event_type = event.event_type
    data = event.data

    if event_type == "phase_change":
        phase = data.get("phase", "unknown")
        round_num = data.get("round", 0)
        print(f"\n{'='*60}")
        print(f"PHASE: {phase.upper()} (Round {round_num})")
        print(f"{'='*60}\n")

    elif event_type == "agent_message":
        agent = data.get("agent", "unknown")
        message = data.get("message", "")
        statement_num = data.get("statement_num", 1)
        print(f"{agent} (statement {statement_num}): {message}\n")

    elif event_type == "vote_cast":
        voter = data.get("voter", "unknown")
        target = data.get("target", "unknown")
        print(f"  {voter} votes for {target}")

    elif event_type == "elimination":
        agent = data.get("agent", "unknown")
        reason = data.get("reason", "unknown")
        role = data.get("role")

        if reason == "killed_at_night":
            print(f"\n[X] {agent} was eliminated by the mafia during the night!")
        elif reason == "voted_out":
            votes = data.get("votes", "?")
            role_str = f" (was {role})" if role else ""
            print(f"\n[X] {agent} was voted out with {votes} votes{role_str}!")

    elif event_type == "game_over":
        winner = data.get("winner", "unknown")
        rounds = data.get("rounds", 0)
        alive = data.get("alive_agents", [])
        print(f"\n{'='*60}")
        print(f"GAME OVER!")
        print(f"{'='*60}")
        print(f"Winner: {winner.upper()}")
        print(f"Rounds: {rounds}")
        print(f"Survivors: {', '.join(alive)}")
        print(f"{'='*60}\n")


async def run_terminal_mode(settings) -> None:
    """Run game in terminal-only mode (existing behavior).

    Args:
        settings: Application settings.
    """
    from src.agents.llm_client import LLMClient
    from src.agents.personalities import ALL_PERSONALITIES
    from src.lobby.manager import LobbyManager

    # Create players via lobby (7 House AI agents)
    llm_client = LLMClient(settings)
    lobby = LobbyManager()
    lobby.fill_with_house_ai(llm_client, ALL_PERSONALITIES)
    players = lobby.get_players()

    # Create game engine with print callback (no betting in terminal mode)
    engine = GameEngine(players, print_event, betting_manager=None)

    # Run game
    print("\n" + "="*60)
    print("MafiaAI - 7 AI Agents Play Mafia (Terminal Mode)")
    print("="*60 + "\n")

    try:
        final_state = await engine.run_game()

        # Print final results
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        print(f"Game ID: {final_state.game_id}")
        print(f"Winner: {final_state.winner}")
        print(f"Total Rounds: {final_state.round_number}")
        print("\nRole Assignments:")
        for agent_name, role in sorted(final_state.role_map.items()):
            status = "[O]" if agent_name in final_state.alive_agents else "[X]"
            print(f"  {status} {agent_name}: {role.value}")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        log.info("game_interrupted")
        print("\n\n[!] Game interrupted by user\n")

    except Exception as exc:
        log.exception("game_error", error=str(exc))
        print(f"\n\n[ERR] Error: {exc}\n")
        raise


async def run_game_with_delay(engine: GameEngine) -> None:
    """Run game after a delay to allow WebSocket clients to connect.

    Args:
        engine: Game engine instance.
    """
    log.info("game_starting_in_3_seconds")
    print("\n[...] Game will start in 3 seconds... Connect WebSocket clients now!")
    print(f"   WebSocket endpoint: ws://localhost:{engine.settings.port}/ws\n")

    await asyncio.sleep(3)

    set_game_active(True)

    try:
        final_state = await engine.run_game()

        # Update routes module with final state
        set_game_state(final_state)

        log.info("game_completed", winner=final_state.winner)
        print(f"\n[OK] Game completed! Winner: {final_state.winner}")

    except Exception as exc:
        log.exception("game_error", error=str(exc))
        set_game_active(False)
        raise
    finally:
        set_game_active(False)


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

    # Create lobby manager
    lobby_manager = LobbyManager()

    # Set betting manager in routes module
    set_betting_manager(betting_manager)

    # Initialize blockchain if enabled
    blockchain_contract = None
    if settings.blockchain_enabled:
        from src.blockchain.contract import MafiaBettingContract
        from src.blockchain.provider import BlockchainProvider

        provider = BlockchainProvider(
            rpc_url=settings.blockchain_rpc_url,
            private_key=settings.blockchain_private_key.get_secret_value(),
            contract_address=settings.blockchain_contract_address,
        )
        if await provider.is_connected():
            blockchain_contract = MafiaBettingContract(provider)
            log.info("blockchain_connected", rpc=settings.blockchain_rpc_url)
        else:
            log.warning("blockchain_connection_failed")

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

    # Start game with lobby logic
    async def start_game_when_ready():
        """Wait for lobby to fill, then start game."""
        lobby_timeout_seconds = getattr(settings, "lobby_timeout_seconds", 30)
        log.info("lobby_waiting", timeout=lobby_timeout_seconds)
        print(f"[...] Lobby waiting for players ({lobby_timeout_seconds}s timeout)...")

        # Wait for lobby timeout
        await asyncio.sleep(lobby_timeout_seconds)

        # Fill remaining slots with House AI
        log.info("filling_with_house_ai")
        lobby_manager.fill_with_house_ai(llm_client, ALL_PERSONALITIES)
        players = lobby_manager.get_players()

        # Broadcast updated lobby status so clients see all players
        from datetime import datetime

        await ws_manager.broadcast(
            WSEvent(
                event_type="lobby_status",
                data={
                    "players": list(players.keys()),
                    "count": len(players),
                    "ready": True,
                },
                game_id=game_id,
                timestamp=datetime.now().isoformat(),
            )
        )

        log.info("game_starting", player_count=len(players))
        print(f"\n[>] Starting game with {len(players)} players...")

        # Create engine with players
        engine = GameEngine(
            players,
            ws_manager.broadcast,
            betting_manager,
            game_id,
            blockchain_contract,
        )

        # Broadcast game starting event
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
                game_id=game_id,
                timestamp=datetime.now().isoformat(),
            )
        )

        set_game_active(True)

        try:
            final_state = await engine.run_game()

            # Update routes module with final state
            set_game_state(final_state)

            log.info("game_completed", winner=final_state.winner)
            print(f"\n[OK] Game completed! Winner: {final_state.winner}")

        except Exception as exc:
            log.exception("game_error", error=str(exc))
            set_game_active(False)
            raise
        finally:
            set_game_active(False)

    game_task = asyncio.create_task(start_game_when_ready())

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
