"""Night phase handler for game state transitions."""

import random
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.config.constants import Phase, Role
from src.models.agent import AgentState
from src.models.events import WSEvent
from src.models.game import GameState, RoundResult
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.players.protocol import PlayerProtocol, TurnContext

log = get_logger(__name__)


async def handle_night(
    state: GameState,
    players: dict[str, "PlayerProtocol"],
    agent_states: dict[str, AgentState],
    event_cb: Callable[[WSEvent], Awaitable[None]],
) -> GameState:
    """Execute night phase: mafia chooses kill, detective investigates.

    Args:
        state: Current game state.
        players: Dict of player name to PlayerProtocol implementation.
        agent_states: Dict of agent name to agent state (for memory/known_roles).
        event_cb: Async callback for broadcasting events.

    Returns:
        New game state with night actions applied.
    """
    log.info("night_phase_start", round=state.round_number)

    # Broadcast phase change
    await event_cb(
        WSEvent(
            event_type="phase_change",
            data={"phase": Phase.NIGHT.value, "round": state.round_number},
            game_id=state.game_id,
            timestamp=datetime.now().isoformat(),
        )
    )

    # Get alive agents
    alive_names = state.alive_agents

    # Mafia choose kill target
    mafia_agents = [name for name in alive_names if state.role_map[name] == Role.MAFIA]
    night_kill = None

    if mafia_agents:
        # Mafia knows each other
        mafia_name = mafia_agents[0]
        mafia_state = agent_states[mafia_name]
        non_mafia_targets = [
            name for name in alive_names if state.role_map[name] != Role.MAFIA
        ]

        if non_mafia_targets:
            # Import here to avoid circular dependency
            from src.players.protocol import TurnContext

            # Build context for mafia player
            ctx = TurnContext(
                alive_agents=state.alive_agents,
                role=Role.MAFIA,
                known_roles=mafia_state.known_roles,
                memory=mafia_state.memory,
                round_number=state.round_number,
                round_history=state.rounds[-3:] if len(state.rounds) >= 3 else state.rounds,
                personality=mafia_state.personality,
            )

            night_kill = await players[mafia_name].night_action(ctx, non_mafia_targets)
            log.info("mafia_kill_chosen", target=night_kill)

    # Detective investigates
    detective_target = None
    detective_result = None

    detective_agents = [
        name for name in alive_names if state.role_map[name] == Role.DETECTIVE
    ]

    if detective_agents:
        detective_name = detective_agents[0]
        detective_state = agent_states[detective_name]
        investigation_targets = [
            name
            for name in alive_names
            if name != detective_name and name not in detective_state.known_roles
        ]

        if investigation_targets:
            # Import here to avoid circular dependency
            from src.players.protocol import TurnContext

            # Build context for detective player
            ctx = TurnContext(
                alive_agents=state.alive_agents,
                role=Role.DETECTIVE,
                known_roles=detective_state.known_roles,
                memory=detective_state.memory,
                round_number=state.round_number,
                round_history=state.rounds[-3:] if len(state.rounds) >= 3 else state.rounds,
                personality=detective_state.personality,
            )

            detective_target = await players[detective_name].night_action(ctx, investigation_targets)
            detective_result = state.role_map[detective_target] == Role.MAFIA
            log.info(
                "detective_investigation",
                target=detective_target,
                is_mafia=detective_result,
            )

    # Apply night kill
    new_alive = tuple(name for name in state.alive_agents if name != night_kill)
    new_dead = (
        (*state.dead_agents, night_kill) if night_kill else state.dead_agents
    )

    # Create round result
    round_result = RoundResult(
        round_number=state.round_number,
        phase=Phase.NIGHT,
        night_kill=night_kill,
        detective_target=detective_target,
        detective_result=detective_result,
    )

    # Broadcast night kill
    if night_kill:
        await event_cb(
            WSEvent(
                event_type="elimination",
                data={
                    "agent": night_kill,
                    "reason": "killed_at_night",
                    "round": state.round_number,
                },
                game_id=state.game_id,
                timestamp=datetime.now().isoformat(),
            )
        )

    # Return new state
    return state.model_copy(
        update={
            "phase": Phase.DAY_DISCUSSION,
            "alive_agents": new_alive,
            "dead_agents": new_dead,
            "rounds": (*state.rounds, round_result),
        }
    )
