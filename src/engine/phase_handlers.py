"""Phase handling logic for game state transitions."""

import random
from collections import Counter
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.config.constants import MAX_DISCUSSION_STATEMENTS, Phase, Role
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


async def handle_day_vote(
    state: GameState,
    players: dict[str, "PlayerProtocol"],
    agent_states: dict[str, AgentState],
    event_cb: Callable[[WSEvent], Awaitable[None]],
) -> GameState:
    """Execute day vote: each alive agent votes to eliminate someone.

    Args:
        state: Current game state.
        players: Dict of player name to PlayerProtocol implementation.
        agent_states: Dict of agent name to agent state (for memory/known_roles).
        event_cb: Async callback for broadcasting events.

    Returns:
        New game state with elimination applied.
    """
    log.info("vote_phase_start", round=state.round_number)

    # Broadcast phase change
    await event_cb(
        WSEvent(
            event_type="phase_change",
            data={"phase": Phase.DAY_VOTE.value, "round": state.round_number},
            game_id=state.game_id,
            timestamp=datetime.now().isoformat(),
        )
    )

    # Import here to avoid circular dependency
    from src.players.protocol import TurnContext

    # Collect votes
    votes: dict[str, str] = {}

    for agent_name in state.alive_agents:
        agent_state = agent_states[agent_name]
        role = state.role_map[agent_name]

        # Vote candidates are all alive agents except self
        candidates = [name for name in state.alive_agents if name != agent_name]

        if candidates:
            # Get recent discussion context
            recent_rounds = state.rounds[-1:] if state.rounds else tuple()

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

            vote = await players[agent_name].vote(ctx, candidates)
            votes[agent_name] = vote

            # Broadcast vote
            await event_cb(
                WSEvent(
                    event_type="vote_cast",
                    data={
                        "voter": agent_name,
                        "target": vote,
                        "round": state.round_number,
                    },
                    game_id=state.game_id,
                    timestamp=datetime.now().isoformat(),
                )
            )

            log.info("vote_cast", voter=agent_name, target=vote)

    # Determine elimination (majority vote)
    vote_counts = Counter(votes.values())
    eliminated = None
    eliminated_role = None

    if vote_counts:
        max_votes = max(vote_counts.values())
        # Get all candidates with max votes
        top_candidates = [
            candidate for candidate, count in vote_counts.items() if count == max_votes
        ]

        # If tie, no elimination; otherwise eliminate the one with most votes
        if len(top_candidates) == 1:
            eliminated = top_candidates[0]
            eliminated_role = state.role_map[eliminated]
            log.info("day_elimination", eliminated=eliminated, role=eliminated_role)
        else:
            log.info("vote_tied", candidates=top_candidates)

    # Apply elimination
    new_alive = (
        tuple(name for name in state.alive_agents if name != eliminated)
        if eliminated
        else state.alive_agents
    )
    new_dead = (*state.dead_agents, eliminated) if eliminated else state.dead_agents

    # Create round result
    round_result = RoundResult(
        round_number=state.round_number,
        phase=Phase.DAY_VOTE,
        eliminated=eliminated,
        eliminated_role=eliminated_role,
        votes=votes,
    )

    # Broadcast elimination
    if eliminated:
        await event_cb(
            WSEvent(
                event_type="elimination",
                data={
                    "agent": eliminated,
                    "role": eliminated_role.value if eliminated_role else None,
                    "reason": "voted_out",
                    "round": state.round_number,
                    "votes": vote_counts[eliminated],
                },
                game_id=state.game_id,
                timestamp=datetime.now().isoformat(),
            )
        )

    # Increment round and return to night phase
    return state.model_copy(
        update={
            "phase": Phase.NIGHT,
            "round_number": state.round_number + 1,
            "alive_agents": new_alive,
            "dead_agents": new_dead,
            "rounds": (*state.rounds, round_result),
        }
    )
