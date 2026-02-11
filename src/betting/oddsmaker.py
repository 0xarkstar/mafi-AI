"""AI-powered odds analysis using LLM."""

from decimal import Decimal

from src.agents.llm_client import LLMClient
from src.config.constants import Role
from src.models.betting import OddsBoard
from src.models.game import GameState
from src.utils.logger import get_logger

log = get_logger(__name__)


async def calculate_ai_odds(game_state: GameState, llm_client: LLMClient) -> OddsBoard:
    """Use AI to analyze game state and generate odds.

    Summarizes game state, sends to LLM, parses response into OddsBoard.
    Fallback: uniform distribution if parsing fails.

    Args:
        game_state: Current game state to analyze.
        llm_client: LLM client for AI analysis.

    Returns:
        OddsBoard with AI-generated odds.
    """
    # Build game summary
    summary = _build_game_summary(game_state)

    try:
        # Get AI odds analysis
        odds_dict = await llm_client.analyze_odds(summary)

        # Parse into OddsBoard fields
        mafia_win_prob = Decimal(str(odds_dict.get("mafia_win", 0.5)))
        citizen_win_prob = Decimal(str(odds_dict.get("citizen_win", 0.5)))

        # Extract mafia suspects (alive agents with probabilities)
        mafia_suspects: dict[str, Decimal] = {}
        for agent_name in game_state.alive_agents:
            prob = odds_dict.get(agent_name, None)
            if prob is not None:
                mafia_suspects[agent_name] = Decimal(str(prob))

        # If no suspects parsed, use uniform distribution
        if not mafia_suspects and game_state.alive_agents:
            uniform_prob = Decimal("1.0") / Decimal(str(len(game_state.alive_agents)))
            mafia_suspects = {
                agent: uniform_prob for agent in game_state.alive_agents
            }

        log.info(
            "ai_odds_calculated",
            mafia_win=float(mafia_win_prob),
            citizen_win=float(citizen_win_prob),
            num_suspects=len(mafia_suspects),
        )

        return OddsBoard(
            game_id=game_state.game_id,
            round_number=game_state.round_number,
            mafia_win_prob=mafia_win_prob,
            citizen_win_prob=citizen_win_prob,
            mafia_suspects=mafia_suspects,
        )

    except Exception as e:
        log.warning("ai_odds_failed", error=str(e), hint="using_fallback")

        # Fallback: uniform distribution
        mafia_suspects = {}
        if game_state.alive_agents:
            uniform_prob = Decimal("1.0") / Decimal(str(len(game_state.alive_agents)))
            mafia_suspects = {
                agent: uniform_prob for agent in game_state.alive_agents
            }

        return OddsBoard(
            game_id=game_state.game_id,
            round_number=game_state.round_number,
            mafia_win_prob=Decimal("0.5"),
            citizen_win_prob=Decimal("0.5"),
            mafia_suspects=mafia_suspects,
        )


def _build_game_summary(game_state: GameState) -> str:
    """Build a text summary of game state for AI analysis.

    Args:
        game_state: Game state to summarize.

    Returns:
        Formatted summary string.
    """
    summary_parts = [
        f"Round: {game_state.round_number}",
        f"Phase: {game_state.phase.value}",
        f"Alive agents: {', '.join(game_state.alive_agents)}",
        f"Dead agents: {', '.join(game_state.dead_agents)}",
    ]

    # Add recent eliminations
    if game_state.rounds:
        recent_rounds = game_state.rounds[-3:]  # Last 3 rounds
        summary_parts.append("\nRecent eliminations:")
        for round_result in recent_rounds:
            if round_result.eliminated:
                role_str = (
                    f" ({round_result.eliminated_role.value})"
                    if round_result.eliminated_role
                    else ""
                )
                summary_parts.append(
                    f"  Round {round_result.round_number}: {round_result.eliminated}{role_str}"
                )

    # Add known mafia count
    mafia_alive = sum(
        1
        for agent in game_state.alive_agents
        if game_state.role_map.get(agent) == Role.MAFIA
    )
    total_mafia = sum(1 for role in game_state.role_map.values() if role == Role.MAFIA)

    summary_parts.append(f"\nMafia remaining: {mafia_alive}/{total_mafia}")

    return "\n".join(summary_parts)
