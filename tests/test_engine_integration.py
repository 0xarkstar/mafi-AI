"""Integration tests for GameEngine in src/engine/game_engine.py."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.constants import Phase, PlayerType, Role
from src.engine.game_engine import GameEngine
from src.models.agent import Personality
from src.models.betting import OddsBoard
from src.models.events import WSEvent
from src.models.game import GameState, RoundResult


# === Helpers ===

PLAYER_NAMES = [f"Agent{i}" for i in range(1, 8)]

# Deterministic role map: Agent1/Agent2 are mafia
FIXED_ROLE_MAP = {
    "Agent1": Role.MAFIA,
    "Agent2": Role.MAFIA,
    "Agent3": Role.DETECTIVE,
    "Agent4": Role.CITIZEN,
    "Agent5": Role.CITIZEN,
    "Agent6": Role.CITIZEN,
    "Agent7": Role.CITIZEN,
}


def make_mock_player(name: str, player_type: PlayerType = PlayerType.HOUSE_AI) -> MagicMock:
    """Create a mock PlayerProtocol implementation."""
    player = MagicMock()
    player.name = name
    player.player_type = player_type
    player.wallet_address = None
    player.personality = Personality(
        name=name,
        trait="player",
        description=f"{name} is playing.",
        speaking_style="casual",
        suspicion_bias=0.5,
    )
    player.generate_statement = AsyncMock(return_value="I think someone is suspicious.")
    player.vote = AsyncMock(return_value="Agent5")
    player.night_action = AsyncMock(return_value="Agent5")
    return player


def make_players() -> dict:
    """Create 7 mock players."""
    return {name: make_mock_player(name) for name in PLAYER_NAMES}


async def noop_callback(event: WSEvent) -> None:
    """No-op event callback."""


def make_state_with_phase(base: GameState, phase: Phase) -> GameState:
    return base.model_copy(update={"phase": phase})


# === Phase handler mocks that preserve game state ===

async def mock_night_handler(state, players, agents, event_cb):
    """Transition NIGHT → DAY_DISCUSSION, no kills."""
    return state.model_copy(update={"phase": Phase.DAY_DISCUSSION})


async def mock_discussion_handler(state, players, agents, event_cb):
    """Transition DAY_DISCUSSION → DAY_VOTE."""
    return state.model_copy(update={"phase": Phase.DAY_VOTE})


async def mock_vote_handler_eliminates_agent1(state, players, agents, event_cb):
    """DAY_VOTE: eliminate Agent1 (mafia), transition → NIGHT with a round result."""
    new_alive = tuple(n for n in state.alive_agents if n != "Agent1")
    new_dead = state.dead_agents + ("Agent1",)
    round_result = RoundResult(
        round_number=state.round_number,
        phase=Phase.DAY_VOTE,
        eliminated="Agent1",
        eliminated_role=Role.MAFIA,
        votes={"Agent3": "Agent1", "Agent4": "Agent1"},
        night_kill=None,
    )
    return state.model_copy(update={
        "phase": Phase.NIGHT,
        "round_number": state.round_number + 1,
        "alive_agents": new_alive,
        "dead_agents": new_dead,
        "rounds": state.rounds + (round_result,),
    })


# === Tests ===


@pytest.mark.asyncio
async def test_citizens_win_immediately():
    """When check_winner returns 'citizens' on first call, game ends immediately."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=collect)
            final_state = await engine.run_game()

    assert final_state.winner == "citizens"
    assert final_state.phase == Phase.REVEAL
    event_types = [e.event_type for e in events]
    assert "phase_change" in event_types  # from _initialize_game
    assert "game_over" in event_types
    assert "identity_reveal" in event_types


@pytest.mark.asyncio
async def test_mafia_wins_immediately():
    """When check_winner returns 'mafia' on first call, game ends immediately."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="mafia"):
            engine = GameEngine(players=players, event_callback=collect)
            final_state = await engine.run_game()

    assert final_state.winner == "mafia"
    event_types = [e.event_type for e in events]
    assert "game_over" in event_types


@pytest.mark.asyncio
async def test_game_uses_provided_game_id():
    """GameEngine uses the pre-provided game_id."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                game_id="fixed-game-id-xyz",
            )
            final_state = await engine.run_game()

    assert final_state.game_id == "fixed-game-id-xyz"


@pytest.mark.asyncio
async def test_game_generates_game_id_when_not_provided():
    """GameEngine auto-generates a game_id when none provided."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=noop_callback)
            final_state = await engine.run_game()

    assert final_state.game_id is not None
    assert len(final_state.game_id) > 0


@pytest.mark.asyncio
async def test_identity_reveals_broadcast_for_all_players():
    """All 7 players get identity_reveal events with correct data."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=collect)
            await engine.run_game()

    reveal_events = [e for e in events if e.event_type == "identity_reveal"]
    assert len(reveal_events) == 7

    # Last event should have all_revealed=True
    assert reveal_events[-1].data["all_revealed"] is True

    # First 6 should have all_revealed=False
    for ev in reveal_events[:-1]:
        assert ev.data["all_revealed"] is False


@pytest.mark.asyncio
async def test_game_over_event_contains_winner_and_rounds():
    """game_over event includes winner and round count."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="mafia"):
            engine = GameEngine(players=players, event_callback=collect)
            await engine.run_game()

    game_over_event = next(e for e in events if e.event_type == "game_over")
    assert game_over_event.data["winner"] == "mafia"
    assert "rounds" in game_over_event.data
    assert "alive_agents" in game_over_event.data


@pytest.mark.asyncio
async def test_betting_manager_none_game_completes():
    """Game completes successfully with betting_manager=None."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                betting_manager=None,
            )
            final_state = await engine.run_game()

    assert final_state.winner == "citizens"


@pytest.mark.asyncio
async def test_betting_manager_settle_called_on_game_over():
    """betting_manager.settle() is called with the winner."""
    players = make_players()

    betting_manager = MagicMock()
    betting_manager.settle = MagicMock(return_value={})
    betting_manager.settle_identity_bets = MagicMock(return_value={})

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                betting_manager=betting_manager,
            )
            await engine.run_game()

    betting_manager.settle.assert_called_once_with("citizens")
    betting_manager.settle_identity_bets.assert_called_once()


@pytest.mark.asyncio
async def test_betting_manager_settle_payouts_in_game_over_event():
    """game_over event includes payout data from betting_manager."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    betting_manager = MagicMock()
    betting_manager.settle = MagicMock(return_value={"0xAddr1": Decimal("10.0")})
    betting_manager.settle_identity_bets = MagicMock(return_value={})

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="mafia"):
            engine = GameEngine(
                players=players,
                event_callback=collect,
                betting_manager=betting_manager,
            )
            await engine.run_game()

    game_over = next(e for e in events if e.event_type == "game_over")
    assert "0xAddr1" in game_over.data["payouts"]
    assert game_over.data["payouts"]["0xAddr1"] == 10.0


@pytest.mark.asyncio
async def test_blockchain_gateway_none_game_completes():
    """Game completes successfully with blockchain_gateway=None."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                blockchain_gateway=None,
            )
            final_state = await engine.run_game()

    assert final_state.winner == "citizens"


@pytest.mark.asyncio
async def test_blockchain_gateway_commit_roles_called():
    """blockchain_gateway.commit_roles() is called during _initialize_game."""
    players = make_players()

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(return_value=None)
    gateway.settle_game = AsyncMock(return_value="0xdeadbeef")

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                blockchain_gateway=gateway,
            )
            await engine.run_game()

    gateway.commit_roles.assert_called_once()


@pytest.mark.asyncio
async def test_blockchain_gateway_lock_betting_called_on_winner():
    """blockchain_gateway.lock_betting() is called when winner is detected."""
    players = make_players()

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(return_value=None)
    gateway.settle_game = AsyncMock(return_value="0xdeadbeef")

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                blockchain_gateway=gateway,
            )
            await engine.run_game()

    gateway.lock_betting.assert_called_once()


@pytest.mark.asyncio
async def test_blockchain_gateway_settle_game_called_with_payouts():
    """blockchain_gateway.settle_game() is called when there are combined payouts."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(return_value=None)
    gateway.settle_game = AsyncMock(return_value="0xabc123")

    betting_manager = MagicMock()
    betting_manager.settle = MagicMock(return_value={"0xAddr1": Decimal("5.0")})
    betting_manager.settle_identity_bets = MagicMock(return_value={})

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=collect,
                betting_manager=betting_manager,
                blockchain_gateway=gateway,
            )
            await engine.run_game()

    gateway.settle_game.assert_called_once()
    blockchain_event = next(
        (e for e in events if e.event_type == "blockchain_settlement"), None
    )
    assert blockchain_event is not None
    assert blockchain_event.data["tx_hash"] == "0xabc123"


@pytest.mark.asyncio
async def test_blockchain_commit_failure_game_continues():
    """If commit_roles raises, game continues without blockchain."""
    players = make_players()

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(side_effect=Exception("RPC error"))
    gateway.lock_betting = AsyncMock(return_value=None)

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                blockchain_gateway=gateway,
            )
            final_state = await engine.run_game()

    # Game still completes even if blockchain fails
    assert final_state.winner == "citizens"


@pytest.mark.asyncio
async def test_blockchain_lock_failure_game_continues():
    """If lock_betting raises, game continues to reveal phase."""
    players = make_players()

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(side_effect=Exception("lock failed"))

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="mafia"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                blockchain_gateway=gateway,
            )
            final_state = await engine.run_game()

    assert final_state.winner == "mafia"


@pytest.mark.asyncio
async def test_game_runs_through_full_round():
    """Game runs NIGHT → DAY_DISCUSSION → DAY_VOTE → win in one round."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    call_counts = {"check": 0}

    def check_winner_side_effect(alive, role_map):
        call_counts["check"] += 1
        # First 3 calls: game ongoing; 4th: citizens win
        if call_counts["check"] <= 3:
            return None
        return "citizens"

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", side_effect=check_winner_side_effect):
            with patch(
                "src.engine.game_engine.handle_night",
                side_effect=mock_night_handler,
            ):
                with patch(
                    "src.engine.game_engine.handle_day_discussion",
                    side_effect=mock_discussion_handler,
                ):
                    with patch(
                        "src.engine.game_engine.handle_day_vote",
                        side_effect=mock_vote_handler_eliminates_agent1,
                    ):
                        engine = GameEngine(players=players, event_callback=collect)
                        final_state = await engine.run_game()

    assert final_state.winner == "citizens"
    assert call_counts["check"] >= 4
    event_types = [e.event_type for e in events]
    assert "game_over" in event_types


@pytest.mark.asyncio
async def test_agents_initialized_with_roles():
    """After _initialize_game, engine.agents has all players with assigned roles."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=noop_callback)
            await engine.run_game()

    assert len(engine.agents) == 7
    for name in PLAYER_NAMES:
        assert name in engine.agents
        assert engine.agents[name].role == FIXED_ROLE_MAP[name]


@pytest.mark.asyncio
async def test_mafia_agents_know_each_other():
    """Mafia agents' known_roles includes all mafia members."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=noop_callback)
            await engine.run_game()

    # Agent1 is mafia — should know Agent2 is mafia
    agent1 = engine.agents["Agent1"]
    assert "Agent1" in agent1.known_roles
    assert "Agent2" in agent1.known_roles
    assert agent1.known_roles["Agent1"] == Role.MAFIA
    assert agent1.known_roles["Agent2"] == Role.MAFIA


@pytest.mark.asyncio
async def test_citizen_agents_have_empty_known_roles():
    """Citizen agents start with empty known_roles."""
    players = make_players()

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=noop_callback)
            await engine.run_game()

    citizen = engine.agents["Agent4"]
    assert citizen.known_roles == {}


@pytest.mark.asyncio
async def test_agents_memory_updated_after_round():
    """Agent memory is updated after a round with eliminations."""
    players = make_players()

    call_counts = {"check": 0}

    def check_winner_side_effect(alive, role_map):
        call_counts["check"] += 1
        if call_counts["check"] <= 3:
            return None
        return "citizens"

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", side_effect=check_winner_side_effect):
            with patch(
                "src.engine.game_engine.handle_night",
                side_effect=mock_night_handler,
            ):
                with patch(
                    "src.engine.game_engine.handle_day_discussion",
                    side_effect=mock_discussion_handler,
                ):
                    with patch(
                        "src.engine.game_engine.handle_day_vote",
                        side_effect=mock_vote_handler_eliminates_agent1,
                    ):
                        engine = GameEngine(players=players, event_callback=noop_callback)
                        await engine.run_game()

    # After a round with elimination, all agents should have memory
    for name, agent in engine.agents.items():
        assert len(agent.memory) > 0, f"{name} should have memory entries"


@pytest.mark.asyncio
async def test_odds_update_events_broadcast_with_betting_manager():
    """odds_update events are broadcast after each phase when betting_manager active."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    odds_board = OddsBoard(game_id="test", round_number=0)

    betting_manager = MagicMock()
    betting_manager.settle = MagicMock(return_value={})
    betting_manager.settle_identity_bets = MagicMock(return_value={})
    betting_manager.update_odds = AsyncMock(return_value=odds_board)

    call_count = {"n": 0}

    def check_winner_side_effect(alive, role_map):
        call_count["n"] += 1
        if call_count["n"] <= 1:
            return None
        return "citizens"

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", side_effect=check_winner_side_effect):
            with patch(
                "src.engine.game_engine.handle_night",
                side_effect=mock_night_handler,
            ):
                engine = GameEngine(
                    players=players,
                    event_callback=collect,
                    betting_manager=betting_manager,
                )
                await engine.run_game()

    betting_manager.update_odds.assert_called()
    odds_events = [e for e in events if e.event_type == "odds_update"]
    assert len(odds_events) >= 1


@pytest.mark.asyncio
async def test_non_house_ai_player_gets_generic_personality():
    """Non-HOUSE_AI players get a generic personality assigned."""
    players = make_players()
    # Make one player a HUMAN type
    players["Agent4"].player_type = PlayerType.HUMAN
    del players["Agent4"].personality  # Remove personality attribute

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(players=players, event_callback=noop_callback)
            await engine.run_game()

    # Human player should have a generic personality created for them
    agent = engine.agents["Agent4"]
    assert agent.personality is not None
    assert agent.personality.name == "Agent4"


@pytest.mark.asyncio
async def test_blockchain_settle_game_failure_does_not_crash():
    """If settle_game raises, game still completes (error logged)."""
    players = make_players()

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(return_value=None)
    gateway.settle_game = AsyncMock(side_effect=Exception("settlement failed"))

    betting_manager = MagicMock()
    betting_manager.settle = MagicMock(return_value={"0xAddr": Decimal("5.0")})
    betting_manager.settle_identity_bets = MagicMock(return_value={})

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=noop_callback,
                betting_manager=betting_manager,
                blockchain_gateway=gateway,
            )
            # Should not raise
            final_state = await engine.run_game()

    assert final_state.winner == "citizens"


@pytest.mark.asyncio
async def test_combined_identity_and_side_win_payouts():
    """Combined payouts from settle() and settle_identity_bets() are merged."""
    players = make_players()
    events = []

    async def collect(event):
        events.append(event)

    gateway = MagicMock()
    gateway.commit_roles = AsyncMock(return_value=None)
    gateway.lock_betting = AsyncMock(return_value=None)
    gateway.settle_game = AsyncMock(return_value="0xabc")

    betting_manager = MagicMock()
    # Both settle() and settle_identity_bets() return payout for same address
    betting_manager.settle = MagicMock(return_value={"0xAddr1": Decimal("5.0")})
    betting_manager.settle_identity_bets = MagicMock(
        return_value={"0xAddr1": Decimal("3.0"), "0xAddr2": Decimal("7.0")}
    )

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", return_value="citizens"):
            engine = GameEngine(
                players=players,
                event_callback=collect,
                betting_manager=betting_manager,
                blockchain_gateway=gateway,
            )
            await engine.run_game()

    # settle_game should be called with combined payouts
    gateway.settle_game.assert_called_once()
    # Check that the call included both addresses
    call_args = gateway.settle_game.call_args
    winners = call_args[0][2] if call_args[0] else call_args[1].get("winners", [])
    amounts = call_args[0][3] if call_args[0] else call_args[1].get("amounts", [])
    assert len(winners) == 2
    assert len(amounts) == 2


@pytest.mark.asyncio
async def test_update_agents_detective_knowledge():
    """Detective's known_roles are updated after investigating a target."""
    players = make_players()

    async def mock_vote_with_detective_result(state, p, agents, event_cb):
        """Vote phase returns a round with detective investigation result."""
        round_result = RoundResult(
            round_number=state.round_number,
            phase=Phase.DAY_VOTE,
            eliminated=None,
            votes={},
            detective_target="Agent1",
            detective_result=True,  # Agent1 is mafia
        )
        return state.model_copy(update={
            "phase": Phase.NIGHT,
            "round_number": state.round_number + 1,
            "rounds": state.rounds + (round_result,),
        })

    call_count = {"n": 0}

    def check_winner_side_effect(alive, role_map):
        call_count["n"] += 1
        if call_count["n"] <= 3:
            return None
        return "citizens"

    with patch("src.engine.game_engine.assign_roles", return_value=FIXED_ROLE_MAP):
        with patch("src.engine.game_engine.check_winner", side_effect=check_winner_side_effect):
            with patch("src.engine.game_engine.handle_night", side_effect=mock_night_handler):
                with patch("src.engine.game_engine.handle_day_discussion", side_effect=mock_discussion_handler):
                    with patch("src.engine.game_engine.handle_day_vote", side_effect=mock_vote_with_detective_result):
                        engine = GameEngine(players=players, event_callback=noop_callback)
                        await engine.run_game()

    # The detective (Agent3) should have Agent1 in their known_roles
    detective = engine.agents["Agent3"]
    assert "Agent1" in detective.known_roles
    assert detective.known_roles["Agent1"] == Role.MAFIA
