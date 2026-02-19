"""Day vote phase handler for game state transitions."""

from collections import Counter
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.config.constants import Phase
from src.models.agent import AgentState
from src.models.events import WSEvent
from src.models.game import GameState, RoundResult
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.players.protocol import PlayerProtocol, TurnContext

log = get_logger(__name__)


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
