"""CLI entry point for MafiaAI game."""

import argparse
import asyncio

import uvicorn

from src.api.routes import set_game_active, set_game_state
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
            print(f"\n💀 {agent} was eliminated by the mafia during the night!")
        elif reason == "voted_out":
            votes = data.get("votes", "?")
            role_str = f" (was {role})" if role else ""
            print(f"\n💀 {agent} was voted out with {votes} votes{role_str}!")

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
    # Create game engine with print callback
    engine = GameEngine(settings, print_event)

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
            status = "✅" if agent_name in final_state.alive_agents else "💀"
            print(f"  {status} {agent_name}: {role.value}")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        log.info("game_interrupted")
        print("\n\n⚠️  Game interrupted by user\n")

    except Exception as exc:
        log.exception("game_error", error=str(exc))
        print(f"\n\n❌ Error: {exc}\n")
        raise


async def run_game_with_delay(engine: GameEngine) -> None:
    """Run game after a delay to allow WebSocket clients to connect.

    Args:
        engine: Game engine instance.
    """
    log.info("game_starting_in_3_seconds")
    print("\n⏳ Game will start in 3 seconds... Connect WebSocket clients now!")
    print(f"   WebSocket endpoint: ws://localhost:{engine.settings.port}/ws\n")

    await asyncio.sleep(3)

    set_game_active(True)

    try:
        final_state = await engine.run_game()

        # Update routes module with final state
        set_game_state(final_state)

        log.info("game_completed", winner=final_state.winner)
        print(f"\n✅ Game completed! Winner: {final_state.winner}")

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
    # Create FastAPI app
    app = create_app(settings, ws_manager)

    # Create game engine with WebSocket broadcast callback
    engine = GameEngine(settings, ws_manager.broadcast)

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

    # Start game in background
    game_task = asyncio.create_task(run_game_with_delay(engine))

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
    if not settings.anthropic_api_key.get_secret_value():
        log.error("anthropic_api_key_missing")
        print("\n❌ Error: ANTHROPIC_API_KEY not set in environment or .env file")
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
