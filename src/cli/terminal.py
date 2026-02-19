"""Terminal mode CLI for MafiaAI game."""

from __future__ import annotations

from src.models.events import WSEvent
from src.utils.logger import get_logger

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
    from src.engine.game_engine import GameEngine
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
