"""Game engine orchestrator managing the main game loop."""

from collections.abc import Awaitable, Callable
from datetime import datetime

from src.agents.claude_client import ClaudeClient
from src.agents.memory import AgentMemory
from src.agents.personalities import ALL_PERSONALITIES
from src.config.constants import Phase, Role
from src.config.settings import Settings
from src.engine.phase_handlers import handle_day_discussion, handle_day_vote, handle_night
from src.engine.role_assigner import assign_roles
from src.engine.win_checker import check_winner
from src.models.agent import AgentState
from src.models.events import WSEvent
from src.models.game import GameState, RoundResult
from src.utils.logger import get_logger

log = get_logger(__name__)


class GameEngine:
    """Orchestrates the game state machine and agent interactions."""

    def __init__(
        self,
        settings: Settings,
        event_callback: Callable[[WSEvent], Awaitable[None]],
        betting_manager=None,
        game_id: str | None = None,
    ):
        """Initialize game engine.

        Args:
            settings: Application settings.
            event_callback: Async callback for broadcasting events.
            betting_manager: Optional betting manager for spectator betting.
            game_id: Optional pre-generated game ID (for server mode with betting).
        """
        self.settings = settings
        self.event_callback = event_callback
        self.claude = ClaudeClient(settings)
        self.state: GameState | None = None
        self.agents: dict[str, AgentState] = {}
        self.betting_manager = betting_manager
        self.game_id = game_id

    async def run_game(self) -> GameState:
        """Run a complete game from start to finish.

        Returns:
            Final game state with winner determined.
        """
        log.info("game_start")

        # Initialize game
        await self._initialize_game()

        # Main game loop
        while self.state and self.state.phase != Phase.GAME_OVER:
            # Check for winner
            winner = check_winner(self.state.alive_agents, self.state.role_map)

            if winner:
                # Game over
                self.state = self.state.model_copy(
                    update={"phase": Phase.GAME_OVER, "winner": winner}
                )

                # Settle bets if betting is enabled
                payouts = {}
                if self.betting_manager:
                    payouts = self.betting_manager.settle(winner)
                    log.info("bets_settled", num_payouts=len(payouts))

                await self.event_callback(
                    WSEvent(
                        event_type="game_over",
                        data={
                            "winner": winner,
                            "rounds": self.state.round_number,
                            "alive_agents": list(self.state.alive_agents),
                            "payouts": {
                                session_id: float(payout)
                                for session_id, payout in payouts.items()
                            },
                        },
                        game_id=self.state.game_id,
                        timestamp=datetime.now().isoformat(),
                    )
                )

                log.info("game_over", winner=winner, rounds=self.state.round_number)
                break

            # Execute phase
            prev_round_count = len(self.state.rounds)

            if self.state.phase == Phase.NIGHT:
                self.state = await handle_night(
                    self.state, self.agents, self.claude, self.event_callback
                )

            elif self.state.phase == Phase.DAY_DISCUSSION:
                self.state = await handle_day_discussion(
                    self.state, self.agents, self.claude, self.event_callback
                )

            elif self.state.phase == Phase.DAY_VOTE:
                self.state = await handle_day_vote(
                    self.state, self.agents, self.claude, self.event_callback
                )

            # Update agent states after phase (memory + detective knowledge)
            if len(self.state.rounds) > prev_round_count:
                latest_round = self.state.rounds[-1]
                self._update_agents_after_round(latest_round)

            # Update odds after phase transition
            if self.betting_manager and self.state:
                odds_board = await self.betting_manager.update_odds(self.state)
                await self.event_callback(
                    WSEvent(
                        event_type="odds_update",
                        data={
                            "mafia_win_prob": float(odds_board.mafia_win_prob),
                            "citizen_win_prob": float(odds_board.citizen_win_prob),
                            "mafia_suspects": {
                                name: float(prob)
                                for name, prob in odds_board.mafia_suspects.items()
                            },
                        },
                        game_id=self.state.game_id,
                        timestamp=datetime.now().isoformat(),
                    )
                )

        return self.state

    async def _initialize_game(self) -> None:
        """Initialize game state and agents."""
        # Assign roles to personalities
        agent_names = [p.name for p in ALL_PERSONALITIES]
        role_map = assign_roles(agent_names)

        log.info("roles_assigned", role_map=role_map)

        # Create agent states
        self.agents = {}
        for personality in ALL_PERSONALITIES:
            role = role_map[personality.name]

            # Mafia agents know each other
            known_roles = {}
            if role == Role.MAFIA:
                known_roles = {
                    name: r for name, r in role_map.items() if r == Role.MAFIA
                }

            self.agents[personality.name] = AgentState(
                name=personality.name,
                personality=personality,
                role=role,
                is_alive=True,
                memory=tuple(),
                known_roles=known_roles,
            )

        # Create initial game state
        state_kwargs = {
            "phase": Phase.NIGHT,  # Start with night phase (round 0)
            "round_number": 0,
            "alive_agents": tuple(agent_names),
            "dead_agents": tuple(),
            "role_map": role_map,
            "rounds": tuple(),
            "winner": None,
        }

        # Use pre-generated game_id if provided
        if self.game_id:
            state_kwargs["game_id"] = self.game_id

        self.state = GameState(**state_kwargs)

        # Broadcast game start
        await self.event_callback(
            WSEvent(
                event_type="phase_change",
                data={
                    "phase": Phase.NIGHT.value,
                    "round": 0,
                    "alive_agents": list(self.state.alive_agents),
                },
                game_id=self.state.game_id,
                timestamp=datetime.now().isoformat(),
            )
        )

        log.info(
            "game_initialized",
            game_id=self.state.game_id,
            agent_count=len(self.agents),
        )

    def _update_agents_after_round(self, result: RoundResult) -> None:
        """Update agent states after a round completes.

        Updates detective's known_roles and all agents' memory.
        """
        # Build memory events from round result
        events: list[str] = []
        if result.night_kill:
            events.append(f"Night {result.round_number}: {result.night_kill} was killed")
        if result.eliminated:
            events.append(
                f"Day {result.round_number}: {result.eliminated} was voted out "
                f"(was {result.eliminated_role.value if result.eliminated_role else 'unknown'})"
            )
        if result.votes:
            vote_summary = ", ".join(f"{v}->{t}" for v, t in result.votes.items())
            events.append(f"Votes: {vote_summary}")

        # Update each agent's memory
        for name, agent in self.agents.items():
            memory = AgentMemory(agent.memory)
            for event in events:
                memory = memory.add(event)

            updates: dict = {"memory": tuple(memory)}

            # Update detective's known_roles after investigation
            if (
                result.detective_target
                and self.state
                and self.state.role_map.get(name) == Role.DETECTIVE
            ):
                new_known = {
                    **agent.known_roles,
                    result.detective_target: self.state.role_map[result.detective_target],
                }
                updates["known_roles"] = new_known

            self.agents[name] = agent.model_copy(update=updates)
