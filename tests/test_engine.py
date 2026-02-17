"""Tests for game engine modules."""

import random
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.constants import Phase, PlayerType, Role
from src.engine.game_engine import GameEngine
from src.engine.phase_handlers import handle_day_discussion, handle_day_vote, handle_night
from src.engine.role_assigner import assign_roles
from src.engine.win_checker import check_winner
from src.models.game import GameState, RoundResult


class TestRoleAssigner:
    """Tests for role assignment logic."""

    def test_correct_role_counts(self):
        """Test that roles are assigned with correct counts."""
        agent_names = [f"Agent{i}" for i in range(7)]
        role_map = assign_roles(agent_names)

        # Count roles
        mafia_count = sum(1 for role in role_map.values() if role == Role.MAFIA)
        detective_count = sum(1 for role in role_map.values() if role == Role.DETECTIVE)
        citizen_count = sum(1 for role in role_map.values() if role == Role.CITIZEN)

        assert mafia_count == 2
        assert detective_count == 1
        assert citizen_count == 4

    def test_wrong_agent_count_raises_error(self):
        """Test that ValueError is raised for wrong agent count."""
        # Too few agents
        with pytest.raises(ValueError, match="Expected 7 agents"):
            assign_roles(["Agent1", "Agent2"])

        # Too many agents
        with pytest.raises(ValueError, match="Expected 7 agents"):
            assign_roles([f"Agent{i}" for i in range(10)])

    def test_deterministic_with_seed(self):
        """Test that role assignment is deterministic with seeded RNG."""
        agent_names = [f"Agent{i}" for i in range(7)]

        # Same seed should produce same assignments
        rng1 = random.Random(42)
        rng2 = random.Random(42)

        role_map1 = assign_roles(agent_names, rng1)
        role_map2 = assign_roles(agent_names, rng2)

        assert role_map1 == role_map2

    def test_all_agents_assigned(self):
        """Test that all agents receive a role."""
        agent_names = [f"Agent{i}" for i in range(7)]
        role_map = assign_roles(agent_names)

        assert set(role_map.keys()) == set(agent_names)
        assert len(role_map) == 7


class TestWinChecker:
    """Tests for win condition checking."""

    def test_citizens_win_all_mafia_dead(self):
        """Test that citizens win when all mafia are dead."""
        alive_agents = ("Agent1", "Agent2", "Agent3")
        role_map = {
            "Agent1": Role.CITIZEN,
            "Agent2": Role.DETECTIVE,
            "Agent3": Role.CITIZEN,
            "Agent4": Role.MAFIA,  # Dead
            "Agent5": Role.MAFIA,  # Dead
        }

        winner = check_winner(alive_agents, role_map)
        assert winner == "citizens"

    def test_mafia_win_equal_numbers(self):
        """Test that mafia win when equal to non-mafia."""
        alive_agents = ("Agent1", "Agent2")
        role_map = {
            "Agent1": Role.MAFIA,
            "Agent2": Role.CITIZEN,
        }

        winner = check_winner(alive_agents, role_map)
        assert winner == "mafia"

    def test_mafia_win_outnumber(self):
        """Test that mafia win when they outnumber non-mafia."""
        alive_agents = ("Agent1", "Agent2", "Agent3")
        role_map = {
            "Agent1": Role.MAFIA,
            "Agent2": Role.MAFIA,
            "Agent3": Role.CITIZEN,
        }

        winner = check_winner(alive_agents, role_map)
        assert winner == "mafia"

    def test_game_ongoing(self):
        """Test that game continues when no win condition met."""
        alive_agents = ("Agent1", "Agent2", "Agent3", "Agent4")
        role_map = {
            "Agent1": Role.MAFIA,
            "Agent2": Role.CITIZEN,
            "Agent3": Role.DETECTIVE,
            "Agent4": Role.CITIZEN,
        }

        winner = check_winner(alive_agents, role_map)
        assert winner is None

    def test_edge_case_1v1_mafia(self):
        """Test edge case: 1 mafia vs 1 citizen."""
        alive_agents = ("Agent1", "Agent2")
        role_map = {
            "Agent1": Role.MAFIA,
            "Agent2": Role.CITIZEN,
        }

        winner = check_winner(alive_agents, role_map)
        assert winner == "mafia"

    def test_edge_case_2v2(self):
        """Test edge case: 2 mafia vs 2 citizens."""
        alive_agents = ("Agent1", "Agent2", "Agent3", "Agent4")
        role_map = {
            "Agent1": Role.MAFIA,
            "Agent2": Role.MAFIA,
            "Agent3": Role.CITIZEN,
            "Agent4": Role.DETECTIVE,
        }

        winner = check_winner(alive_agents, role_map)
        assert winner == "mafia"


class TestPhaseHandlers:
    """Tests for phase handler functions."""

    @pytest.mark.asyncio
    async def test_handle_night_produces_events(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_night produces correct events."""
        callback, events = event_collector

        # Configure mock players to return valid targets
        for name, player in mock_players.items():
            player.night_action = AsyncMock(
                side_effect=["TestAgent4", "TestAgent5"]  # Kill, investigate
            )

        new_state = await handle_night(
            sample_game_state, mock_players, sample_agents, callback
        )

        # Check events
        assert len(events) >= 1  # At least phase_change event
        assert events[0].event_type == "phase_change"
        assert events[0].data["phase"] == Phase.NIGHT.value

        # Check state transition
        assert new_state.phase == Phase.DAY_DISCUSSION
        assert new_state is not sample_game_state  # Immutability

    @pytest.mark.asyncio
    async def test_handle_night_kills_target(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_night applies night kill correctly."""
        callback, events = event_collector

        # Mafia kills TestAgent4
        for name, player in mock_players.items():
            player.night_action = AsyncMock(
                side_effect=["TestAgent4", "TestAgent5"]
            )

        new_state = await handle_night(
            sample_game_state, mock_players, sample_agents, callback
        )

        # Check that TestAgent4 is dead
        assert "TestAgent4" not in new_state.alive_agents
        assert "TestAgent4" in new_state.dead_agents

        # Check round result
        assert len(new_state.rounds) == 1
        round_result = new_state.rounds[0]
        assert round_result.night_kill == "TestAgent4"
        assert round_result.phase == Phase.NIGHT

    @pytest.mark.asyncio
    async def test_handle_night_detective_investigates(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that detective investigation is recorded."""
        callback, events = event_collector

        # Configure mocks: TestAgent1 (mafia) kills TestAgent5, TestAgent3 (detective) investigates TestAgent1
        mock_players["TestAgent1"].night_action = AsyncMock(return_value="TestAgent5")
        mock_players["TestAgent3"].night_action = AsyncMock(return_value="TestAgent1")

        new_state = await handle_night(
            sample_game_state, mock_players, sample_agents, callback
        )

        # Check investigation result
        round_result = new_state.rounds[0]
        assert round_result.detective_target == "TestAgent1"
        assert round_result.detective_result is True  # TestAgent1 is mafia

    @pytest.mark.asyncio
    async def test_handle_night_returns_new_state(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_night returns new immutable state."""
        callback, _ = event_collector

        for name, player in mock_players.items():
            player.night_action = AsyncMock(
                side_effect=["TestAgent4", "TestAgent5"]
            )

        new_state = await handle_night(
            sample_game_state, mock_players, sample_agents, callback
        )

        # Verify immutability
        assert new_state is not sample_game_state
        assert sample_game_state.phase == Phase.NIGHT  # Original unchanged
        assert new_state.phase == Phase.DAY_DISCUSSION  # New state changed

    @pytest.mark.asyncio
    async def test_handle_day_discussion_produces_messages(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_day_discussion produces agent messages."""
        callback, events = event_collector

        # Set state to DAY_DISCUSSION
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_DISCUSSION})

        for name, player in mock_players.items():
            player.generate_statement = AsyncMock(
                return_value="I think someone is suspicious."
            )

        new_state = await handle_day_discussion(
            state, mock_players, sample_agents, callback
        )

        # Check that agent messages were generated
        message_events = [e for e in events if e.event_type == "agent_message"]
        assert len(message_events) == 7 * 2  # 7 agents * 2 statements each

        # Check state transition
        assert new_state.phase == Phase.DAY_VOTE

    @pytest.mark.asyncio
    async def test_handle_day_discussion_returns_new_state(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_day_discussion returns new state."""
        callback, _ = event_collector
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_DISCUSSION})

        new_state = await handle_day_discussion(
            state, mock_players, sample_agents, callback
        )

        # Verify immutability
        assert new_state is not state
        assert new_state.phase == Phase.DAY_VOTE

    @pytest.mark.asyncio
    async def test_handle_day_vote_eliminates_majority(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_day_vote eliminates agent with majority."""
        callback, events = event_collector
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_VOTE})

        # 5 agents vote for TestAgent4, 2 vote for TestAgent5
        votes = [
            "TestAgent4",  # TestAgent1 votes
            "TestAgent4",  # TestAgent2 votes
            "TestAgent4",  # TestAgent3 votes
            "TestAgent5",  # TestAgent4 votes
            "TestAgent4",  # TestAgent5 votes
            "TestAgent5",  # TestAgent6 votes
            "TestAgent4",  # TestAgent7 votes
        ]
        for name, player in mock_players.items():
            player.vote = AsyncMock(side_effect=votes)

        new_state = await handle_day_vote(
            state, mock_players, sample_agents, callback
        )

        # Check elimination
        assert "TestAgent4" not in new_state.alive_agents
        assert "TestAgent4" in new_state.dead_agents

        # Check round result
        round_result = new_state.rounds[0]
        assert round_result.eliminated == "TestAgent4"
        assert round_result.eliminated_role == Role.CITIZEN

    @pytest.mark.asyncio
    async def test_handle_day_vote_no_elimination_on_tie(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that no elimination occurs on tied vote."""
        callback, _ = event_collector
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_VOTE})

        # Create a tie: 3 votes for TestAgent4, 3 for TestAgent5, 1 for TestAgent6
        # Configure each player's vote individually
        mock_players["TestAgent1"].vote = AsyncMock(return_value="TestAgent4")
        mock_players["TestAgent2"].vote = AsyncMock(return_value="TestAgent4")
        mock_players["TestAgent3"].vote = AsyncMock(return_value="TestAgent4")
        mock_players["TestAgent4"].vote = AsyncMock(return_value="TestAgent5")
        mock_players["TestAgent5"].vote = AsyncMock(return_value="TestAgent5")
        mock_players["TestAgent6"].vote = AsyncMock(return_value="TestAgent5")
        mock_players["TestAgent7"].vote = AsyncMock(return_value="TestAgent6")

        new_state = await handle_day_vote(
            state, mock_players, sample_agents, callback
        )

        # No one should be eliminated (TestAgent4 and TestAgent5 both have 3 votes - tie)
        assert len(new_state.alive_agents) == 7
        assert len(new_state.dead_agents) == 0

        # Round result should show no elimination
        round_result = new_state.rounds[0]
        assert round_result.eliminated is None

    @pytest.mark.asyncio
    async def test_handle_day_vote_increments_round(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_day_vote increments round number."""
        callback, _ = event_collector
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_VOTE})

        votes = ["TestAgent4"] * 7  # Everyone votes for TestAgent4
        for name, player in mock_players.items():
            player.vote = AsyncMock(side_effect=votes)

        new_state = await handle_day_vote(
            state, mock_players, sample_agents, callback
        )

        # Round should increment
        assert new_state.round_number == 1
        assert state.round_number == 0

        # Phase should return to NIGHT
        assert new_state.phase == Phase.NIGHT

    @pytest.mark.asyncio
    async def test_handle_day_vote_returns_new_state(
        self, sample_game_state, sample_agents, mock_players, event_collector
    ):
        """Test that handle_day_vote returns new immutable state."""
        callback, _ = event_collector
        state = sample_game_state.model_copy(update={"phase": Phase.DAY_VOTE})

        votes = ["TestAgent4"] * 7
        for name, player in mock_players.items():
            player.vote = AsyncMock(side_effect=votes)

        new_state = await handle_day_vote(
            state, mock_players, sample_agents, callback
        )

        # Verify immutability
        assert new_state is not state
        assert state.phase == Phase.DAY_VOTE  # Original unchanged
        assert new_state.phase == Phase.NIGHT  # New state changed


class TestGameEngineV2Lifecycle:
    """Tests for V2 blockchain lifecycle integration in GameEngine."""

    def _make_engine(self, mock_players, blockchain_gateway=None, betting_manager=None,
                     event_callback=None):
        """Helper to create a GameEngine with mocked dependencies."""
        return GameEngine(
            players=mock_players,
            event_callback=event_callback or AsyncMock(),
            betting_manager=betting_manager,
            game_id="test-game-v2",
            blockchain_gateway=blockchain_gateway,
        )

    def _setup_citizens_win(self, engine):
        """Set engine.state so citizens have already won (no mafia alive)."""
        role_map = engine.state.role_map
        alive = tuple(n for n in engine.state.alive_agents if role_map[n] != Role.MAFIA)
        dead = tuple(n for n in engine.state.alive_agents if role_map[n] == Role.MAFIA)
        engine.state = engine.state.model_copy(
            update={"alive_agents": alive, "dead_agents": dead}
        )

    async def _init_engine(self, engine, mock_players):
        """Initialize engine with patched role assignment, skip re-init in run_game."""
        with patch("src.engine.game_engine.assign_roles") as mock_assign:
            role_map = {name: Role.CITIZEN for name in mock_players}
            names = list(mock_players.keys())
            role_map[names[0]] = Role.MAFIA
            role_map[names[1]] = Role.MAFIA
            role_map[names[2]] = Role.DETECTIVE
            mock_assign.return_value = role_map
            await engine._initialize_game()

    @pytest.mark.asyncio
    async def test_initialize_calls_commit_roles(self, mock_players):
        """Test that _initialize_game calls blockchain_gateway.commit_roles."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        engine = self._make_engine(mock_players, blockchain_gateway=gateway)

        await self._init_engine(engine, mock_players)

        gateway.commit_roles.assert_called_once()
        call_args = gateway.commit_roles.call_args
        assert call_args[0][0] == "test-game-v2"
        assert isinstance(call_args[0][1], dict)

    @pytest.mark.asyncio
    async def test_initialize_continues_on_blockchain_failure(self, mock_players):
        """Test that game continues if blockchain_gateway.commit_roles fails."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(side_effect=Exception("RPC down"))
        engine = self._make_engine(mock_players, blockchain_gateway=gateway)

        await self._init_engine(engine, mock_players)

        assert engine.state is not None
        assert engine.state.phase == Phase.NIGHT

    @pytest.mark.asyncio
    async def test_lock_betting_called_on_game_over(self, mock_players):
        """Test that lock_betting is called when a winner is found."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        gateway.lock_betting = AsyncMock(return_value="0xdef")
        gateway.settle_game = AsyncMock(return_value="0x123")

        engine = self._make_engine(mock_players, blockchain_gateway=gateway)
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)

        # Patch _initialize_game so run_game doesn't re-init
        engine._initialize_game = AsyncMock()

        await engine.run_game()

        gateway.lock_betting.assert_called_once_with("test-game-v2")

    @pytest.mark.asyncio
    async def test_lock_betting_failure_does_not_crash(self, mock_players):
        """Test that lock_betting failure doesn't prevent game completion."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        gateway.lock_betting = AsyncMock(side_effect=Exception("lock failed"))

        engine = self._make_engine(mock_players, blockchain_gateway=gateway)
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        result = await engine.run_game()
        assert result.winner == "citizens"

    @pytest.mark.asyncio
    async def test_settle_game_called_with_combined_payouts(self, mock_players):
        """Test that settle_game is called with winner addresses and amounts."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        gateway.lock_betting = AsyncMock(return_value="0xdef")
        gateway.settle_game = AsyncMock(return_value="0x456")

        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xWinner1": Decimal("10.5")})
        betting_mgr.settle_identity_bets = MagicMock(
            return_value={"0xWinner1": Decimal("2.0"), "0xWinner2": Decimal("5.0")}
        )
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players, blockchain_gateway=gateway, betting_manager=betting_mgr
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        await engine.run_game()

        gateway.settle_game.assert_called_once()
        call_args = gateway.settle_game.call_args
        assert call_args[0][0] == "test-game-v2"
        winners = call_args[0][2]
        amounts = call_args[0][3]
        assert "0xWinner1" in winners
        assert "0xWinner2" in winners
        assert len(winners) == 2
        assert len(amounts) == 2

    @pytest.mark.asyncio
    async def test_settle_game_failure_does_not_crash(self, mock_players):
        """Test that settle_game failure doesn't crash the game."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        gateway.lock_betting = AsyncMock(return_value="0xdef")
        gateway.settle_game = AsyncMock(side_effect=Exception("settle failed"))

        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xA": Decimal("5.0")})
        betting_mgr.settle_identity_bets = MagicMock(return_value={})
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players, blockchain_gateway=gateway, betting_manager=betting_mgr
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        result = await engine.run_game()
        assert result.winner == "citizens"

    @pytest.mark.asyncio
    async def test_no_blockchain_uses_legacy_settlement(self, mock_players):
        """Test that without gateway, legacy USDCSettlement path is used."""
        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xA": Decimal("5.0")})
        betting_mgr.settle_identity_bets = MagicMock(
            return_value={"0xB": Decimal("3.0")}
        )
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players, blockchain_gateway=None, betting_manager=betting_mgr
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        with patch("src.config.settings.load_settings") as mock_settings:
            mock_settings.return_value = MagicMock(settlement_enabled=False)
            result = await engine.run_game()

        assert result.winner == "citizens"

    @pytest.mark.asyncio
    async def test_blockchain_settlement_event_broadcast(self, mock_players):
        """Test that blockchain_settlement event is broadcast after V2 settle."""
        gateway = AsyncMock()
        gateway.commit_roles = AsyncMock(return_value="0xabc")
        gateway.lock_betting = AsyncMock(return_value="0xdef")
        gateway.settle_game = AsyncMock(return_value="0x789")

        events = []

        async def collect_event(event):
            events.append(event)

        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xA": Decimal("5.0")})
        betting_mgr.settle_identity_bets = MagicMock(return_value={})
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players,
            blockchain_gateway=gateway,
            betting_manager=betting_mgr,
            event_callback=collect_event,
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        await engine.run_game()

        settlement_events = [
            e for e in events if e.event_type == "blockchain_settlement"
        ]
        assert len(settlement_events) == 1
        assert settlement_events[0].data["tx_hash"] == "0x789"
        assert settlement_events[0].data["winners"] == ["0xA"]

    @pytest.mark.asyncio
    async def test_no_gateway_no_lock_no_settle(self, mock_players):
        """Test that without gateway, lock_betting and settle_game are not called."""
        engine = self._make_engine(mock_players, blockchain_gateway=None)
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        result = await engine.run_game()
        assert result.winner == "citizens"
        # No gateway means no blockchain calls — just verify no exception

    @pytest.mark.asyncio
    async def test_legacy_settlement_enabled_path(self, mock_players):
        """Test legacy USDC settlement when settlement_enabled=True, no gateway."""
        events = []

        async def collect_event(event):
            events.append(event)

        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xA": Decimal("5.0")})
        betting_mgr.settle_identity_bets = MagicMock(
            return_value={"0xB": Decimal("3.0")}
        )
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players,
            blockchain_gateway=None,
            betting_manager=betting_mgr,
            event_callback=collect_event,
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        mock_settlement = AsyncMock(return_value=[
            {"address": "0xA", "amount": 5.0, "tx_hash": "0xaaa"},
            {"address": "0xB", "amount": 3.0, "tx_hash": "0xbbb"},
        ])

        with patch("src.config.settings.load_settings") as mock_settings, \
             patch("src.betting.settlement.USDCSettlement") as mock_usdc_cls, \
             patch("src.blockchain.provider.create_web3_provider", new_callable=AsyncMock):
            mock_settings.return_value = MagicMock(
                settlement_enabled=True,
                blockchain_rpc_url="https://rpc",
                blockchain_chain_id=10143,
                x402_usdc_address="0xUSDC",
                settlement_private_key=MagicMock(get_secret_value=MagicMock(return_value="0x" + "a" * 64)),
            )
            mock_usdc_cls.return_value = MagicMock(
                settle_payouts=mock_settlement,
            )

            result = await engine.run_game()

        assert result.winner == "citizens"
        # Verify USDC settlement was called
        mock_settlement.assert_called_once()
        # Verify usdc_settlement event was broadcast
        settlement_events = [e for e in events if e.event_type == "usdc_settlement"]
        assert len(settlement_events) == 1

    @pytest.mark.asyncio
    async def test_legacy_settlement_failure_handled(self, mock_players):
        """Test legacy USDC settlement catches exceptions gracefully."""
        betting_mgr = MagicMock()
        betting_mgr.settle = MagicMock(return_value={"0xA": Decimal("5.0")})
        betting_mgr.settle_identity_bets = MagicMock(
            return_value={"0xA": Decimal("2.0")}
        )
        betting_mgr.update_odds = AsyncMock()

        engine = self._make_engine(
            mock_players, blockchain_gateway=None, betting_manager=betting_mgr
        )
        await self._init_engine(engine, mock_players)
        self._setup_citizens_win(engine)
        engine._initialize_game = AsyncMock()

        with patch("src.config.settings.load_settings") as mock_settings, \
             patch("src.betting.settlement.USDCSettlement", side_effect=Exception("USDC init failed")), \
             patch("src.blockchain.provider.create_web3_provider", new_callable=AsyncMock):
            mock_settings.return_value = MagicMock(
                settlement_enabled=True,
                blockchain_rpc_url="https://rpc",
                blockchain_chain_id=10143,
                x402_usdc_address="0xUSDC",
                settlement_private_key=MagicMock(get_secret_value=MagicMock(return_value="0x" + "a" * 64)),
            )

            # Should not raise — errors are caught
            result = await engine.run_game()

        assert result.winner == "citizens"
