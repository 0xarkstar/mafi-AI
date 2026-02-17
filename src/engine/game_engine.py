"""Game engine orchestrator managing the main game loop."""

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import TYPE_CHECKING

from src.agents.memory import AgentMemory
from src.config.constants import Phase, PlayerType, Role
from src.engine.phase_handlers import handle_day_discussion, handle_day_vote, handle_night
from src.engine.role_assigner import assign_roles
from src.engine.win_checker import check_winner
from src.models.agent import AgentState, Personality
from src.models.events import WSEvent
from src.models.game import GameState, RoundResult
from src.utils.logger import get_logger

if TYPE_CHECKING:
    from src.players.protocol import PlayerProtocol

log = get_logger(__name__)


class GameEngine:
    """Orchestrates the game state machine and agent interactions."""

    def __init__(
        self,
        players: dict[str, "PlayerProtocol"],
        event_callback: Callable[[WSEvent], Awaitable[None]],
        betting_manager=None,
        game_id: str | None = None,
        blockchain_gateway=None,
    ):
        """Initialize game engine.

        Args:
            players: Dict of player name to PlayerProtocol implementation.
            event_callback: Async callback for broadcasting events.
            betting_manager: Optional betting manager for spectator betting.
            game_id: Optional pre-generated game ID (for server mode with betting).
            blockchain_gateway: Optional blockchain gateway for V2 on-chain operations.
        """
        self.players = players
        self.event_callback = event_callback
        self.state: GameState | None = None
        self.agents: dict[str, AgentState] = {}
        self.betting_manager = betting_manager
        self.game_id = game_id
        self.blockchain_gateway = blockchain_gateway

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

                # Settle bets if betting is enabled (calculate payouts only)
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

                # Transition to REVEAL phase to show player identities
                self.state = self.state.model_copy(update={"phase": Phase.REVEAL})

                # Broadcast identity reveals
                player_items = list(self.players.items())
                for idx, (name, player) in enumerate(player_items):
                    is_last = idx == len(player_items) - 1
                    await self.event_callback(
                        WSEvent(
                            event_type="identity_reveal",
                            data={
                                "player_name": name,
                                "name": name,
                                "player_type": player.player_type.value,
                                "role": self.state.role_map[name].value,
                                "all_revealed": is_last,
                            },
                            game_id=self.state.game_id,
                            timestamp=datetime.now().isoformat(),
                        )
                    )

                # Settle identity bets
                identity_payouts = {}
                if self.betting_manager:
                    identity_payouts = self.betting_manager.settle_identity_bets(self.players)
                    log.info("identity_bets_settled", num_payouts=len(identity_payouts))

                    # Combine payouts from both side_win and identity bets
                    combined_payouts = payouts.copy()
                    for address, amount in identity_payouts.items():
                        if address in combined_payouts:
                            combined_payouts[address] += amount
                        else:
                            combined_payouts[address] = amount

                    # Transfer USDC to winners if settlement is enabled
                    if combined_payouts:
                        from src.config.settings import load_settings

                        settings = load_settings()

                        if settings.settlement_enabled:
                            try:
                                from src.betting.settlement import USDCSettlement
                                from src.blockchain.provider import create_web3_provider

                                # Initialize web3 provider
                                w3 = await create_web3_provider(
                                    settings.blockchain_rpc_url, settings.blockchain_chain_id
                                )

                                # Initialize USDC settlement
                                settlement = USDCSettlement(
                                    w3=w3,
                                    usdc_address=settings.x402_usdc_address,
                                    private_key=settings.settlement_private_key.get_secret_value(),
                                )

                                # Transfer USDC to winners
                                transfer_results = await settlement.settle_payouts(combined_payouts)

                                log.info(
                                    "usdc_settlement_complete",
                                    num_transfers=len(transfer_results),
                                )

                                # Broadcast settlement results
                                await self.event_callback(
                                    WSEvent(
                                        event_type="usdc_settlement",
                                        data={
                                            "transfers": transfer_results,
                                        },
                                        game_id=self.state.game_id,
                                        timestamp=datetime.now().isoformat(),
                                    )
                                )

                            except Exception as exc:
                                log.error(
                                    "usdc_settlement_failed",
                                    error=str(exc),
                                )
                        else:
                            log.info(
                                "usdc_settlement_disabled",
                                total_payouts=float(sum(combined_payouts.values())),
                            )

                log.info("reveal_phase_complete", player_count=len(self.players))
                break

            # Execute phase
            prev_round_count = len(self.state.rounds)

            if self.state.phase == Phase.NIGHT:
                self.state = await handle_night(
                    self.state, self.players, self.agents, self.event_callback
                )

            elif self.state.phase == Phase.DAY_DISCUSSION:
                self.state = await handle_day_discussion(
                    self.state, self.players, self.agents, self.event_callback
                )

            elif self.state.phase == Phase.DAY_VOTE:
                self.state = await handle_day_vote(
                    self.state, self.players, self.agents, self.event_callback
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
        # Get player names from the players dict
        agent_names = list(self.players.keys())
        role_map = assign_roles(agent_names)

        log.info("roles_assigned", role_map=role_map)

        # Create agent states for each player
        self.agents = {}
        for name, player in self.players.items():
            role = role_map[name]

            # Mafia agents know each other
            known_roles = {}
            if role == Role.MAFIA:
                known_roles = {
                    n: r for n, r in role_map.items() if r == Role.MAFIA
                }

            # Get personality if the player is a House AI, otherwise use a generic personality
            personality = None
            if player.player_type == PlayerType.HOUSE_AI and hasattr(player, 'personality'):
                personality = player.personality
            else:
                # Create a generic personality for non-AI players
                personality = Personality(
                    name=name,
                    trait="player",
                    description=f"{name} is playing the game.",
                    speaking_style="casual",
                    suspicion_bias=0.5,
                )

            self.agents[name] = AgentState(
                name=name,
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

        # Create game on-chain with commit-reveal if blockchain is enabled
        if self.blockchain_gateway:
            try:
                await self.blockchain_gateway.commit_roles(self.state.game_id, role_map)
                log.info("blockchain_game_created", game_id=self.state.game_id)
            except Exception as exc:
                log.warning(
                    "blockchain_create_failed",
                    error=str(exc),
                    msg="Game will continue without blockchain",
                )

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

    def _uuid_to_uint256(self, uuid_str: str) -> int:
        """Convert UUID game_id to uint256 for smart contract.

        Args:
            uuid_str: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000").

        Returns:
            Integer representation suitable for uint256.
        """
        # Remove hyphens and convert to int, then mod to keep manageable
        return int(uuid_str.replace("-", ""), 16) % (2**64)
