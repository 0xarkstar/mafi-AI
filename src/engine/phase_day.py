"""Day discussion phase handler for game state transitions."""

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.config.constants import MAX_DISCUSSION_STATEMENTS, Phase
from src.models.agent import AgentState
from src.models.events import WSEvent
from src.models.game import GameState
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.players.protocol import PlayerProtocol, TurnContext

log = get_logger(__name__)


async def handle_day_discussion(
    state: GameState,
    players: dict[str, "PlayerProtocol"],
    agent_states: dict[str, AgentState],
    event_cb: Callable[[WSEvent], Awaitable[None]],
) -> GameState:
    """Execute day discussion: each alive agent speaks.

    Args:
        state: Current game state.
        players: Dict of player name to PlayerProtocol implementation.
        agent_states: Dict of agent name to agent state (for memory/known_roles).
        event_cb: Async callback for broadcasting events.

    Returns:
        New game state (phase changed to DAY_VOTE).
    """
    log.info("discussion_phase_start", round=state.round_number)

    # Broadcast phase change
    await event_cb(
        WSEvent(
            event_type="phase_change",
            data={"phase": Phase.DAY_DISCUSSION.value, "round": state.round_number},
            game_id=state.game_id,
            timestamp=datetime.now().isoformat(),
        )
    )

    # Get recent round events for context
    recent_rounds = state.rounds[-3:] if len(state.rounds) >= 3 else state.rounds

    # Import here to avoid circular dependency
    from src.players.protocol import TurnContext

    # Each alive agent speaks
    for agent_name in state.alive_agents:
        agent_state = agent_states[agent_name]
        role = state.role_map[agent_name]

        # Build context for player
        ctx = TurnContext(
            alive_agents=state.alive_agents,
            role=role,
            known_roles=agent_state.known_roles,
            memory=agent_state.memory,
            round_number=state.round_number,
            round_history=recent_rounds,
            personality=agent_state.personality,
        )

        # Generate statements (up to MAX_DISCUSSION_STATEMENTS)
        for statement_num in range(MAX_DISCUSSION_STATEMENTS):
            statement = await players[agent_name].generate_statement(ctx)

            # Broadcast statement
            await event_cb(
                WSEvent(
                    event_type="agent_message",
                    data={
                        "agent": agent_name,
                        "message": statement,
                        "round": state.round_number,
                        "statement_num": statement_num + 1,
                    },
                    game_id=state.game_id,
                    timestamp=datetime.now().isoformat(),
                )
            )

            log.info(
                "agent_statement",
                agent=agent_name,
                statement_num=statement_num + 1,
                statement=statement[:100],
            )

    # Return new state with phase changed
    return state.model_copy(update={"phase": Phase.DAY_VOTE})
