"""Tests for AI Bettor module."""

import time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.ai_bettor.analyzer import GameAnalyzer
from src.ai_bettor.client import AIBettorClient
from src.ai_bettor.models import AIBettorState, BetDecision, GameObservation
from src.ai_bettor.strategy import BettingStrategy


# === Models Tests ===


def test_game_observation_frozen():
    """GameObservation should be immutable."""
    obs = GameObservation(
        game_id="game123",
        phase="day_discussion",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=("charlie",),
        recent_events=("event1",),
        current_odds={"alice": Decimal("2.5")},
    )

    with pytest.raises(Exception):  # Pydantic raises ValidationError or AttributeError
        obs.phase = "night"


def test_bet_decision_frozen():
    """BetDecision should be immutable."""
    decision = BetDecision(
        should_bet=True,
        bet_type="side_win",
        target="citizens",
        amount_usdc=Decimal("5.00"),
        confidence=0.8,
        reasoning="Test reasoning",
    )

    with pytest.raises(Exception):
        decision.should_bet = False


def test_ai_bettor_state_frozen():
    """AIBettorState should be immutable."""
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    with pytest.raises(Exception):
        state.balance_usdc = Decimal("50.00")


# === Strategy Tests ===


def test_strategy_should_bet_in_betting_phase():
    """Should allow betting during day_discussion phase."""
    observation = GameObservation(
        game_id="game123",
        phase="day_discussion",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is True


def test_strategy_should_bet_in_day_vote_phase():
    """Should allow betting during day_vote phase."""
    observation = GameObservation(
        game_id="game123",
        phase="day_vote",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is True


def test_strategy_should_not_bet_in_lobby():
    """Should not allow betting during lobby phase."""
    observation = GameObservation(
        game_id="game123",
        phase="lobby",
        round_number=0,
        alive_agents=(),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False


def test_strategy_should_not_bet_in_night():
    """Should not allow betting during night phase."""
    observation = GameObservation(
        game_id="game123",
        phase="night",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False


def test_strategy_should_not_bet_in_game_over():
    """Should not allow betting during game_over phase."""
    observation = GameObservation(
        game_id="game123",
        phase="game_over",
        round_number=3,
        alive_agents=("alice",),
        dead_agents=("bob", "charlie"),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False


def test_strategy_should_not_bet_in_reveal():
    """Should not allow betting during reveal phase."""
    observation = GameObservation(
        game_id="game123",
        phase="reveal",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=0,
        last_bet_time=None,
        total_wagered=Decimal("0"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False


def test_strategy_should_not_bet_with_zero_balance():
    """Should not allow betting with zero balance."""
    observation = GameObservation(
        game_id="game123",
        phase="day_discussion",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )
    state = AIBettorState(
        balance_usdc=Decimal("0"),
        bets_placed=5,
        last_bet_time=None,
        total_wagered=Decimal("100.00"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False


def test_strategy_cooldown_enforcement():
    """Should enforce 30s cooldown between bets."""
    observation = GameObservation(
        game_id="game123",
        phase="day_discussion",
        round_number=1,
        alive_agents=("alice", "bob"),
        dead_agents=(),
        recent_events=(),
        current_odds={},
    )

    # Just placed bet 10s ago
    recent_bet_time = time.time() - 10
    state = AIBettorState(
        balance_usdc=Decimal("100.00"),
        bets_placed=1,
        last_bet_time=recent_bet_time,
        total_wagered=Decimal("5.00"),
        total_won=Decimal("0"),
    )

    strategy = BettingStrategy()
    assert strategy.should_bet_now(observation, state) is False

    # Bet placed 31s ago - cooldown passed
    old_bet_time = time.time() - 31
    state_after_cooldown = state.model_copy(update={"last_bet_time": old_bet_time})
    assert strategy.should_bet_now(observation, state_after_cooldown) is True


def test_strategy_calculate_amount_min_confidence():
    """Should return $1 at minimum confidence (0.6)."""
    strategy = BettingStrategy()
    amount = strategy.calculate_amount(0.6, Decimal("100.00"))
    assert amount == Decimal("1.00")


def test_strategy_calculate_amount_max_confidence():
    """Should return $10 at maximum confidence (1.0)."""
    strategy = BettingStrategy()
    amount = strategy.calculate_amount(1.0, Decimal("100.00"))
    assert amount == Decimal("10.00")


def test_strategy_calculate_amount_mid_confidence():
    """Should return $5.50 at mid confidence (0.8)."""
    strategy = BettingStrategy()
    amount = strategy.calculate_amount(0.8, Decimal("100.00"))
    # Linear: 0.6→1.0 maps to $1→$10
    # 0.8 is halfway between 0.6 and 1.0: (0.8-0.6)/(1.0-0.6) = 0.5
    # Amount = 1 + 9*0.5 = 5.50
    assert amount == Decimal("5.50")


def test_strategy_calculate_amount_below_threshold():
    """Should return $0 if confidence below 0.6."""
    strategy = BettingStrategy()
    amount = strategy.calculate_amount(0.5, Decimal("100.00"))
    assert amount == Decimal("0")


def test_strategy_calculate_amount_exceeds_balance():
    """Should return $0 if calculated amount exceeds balance."""
    strategy = BettingStrategy()
    # With balance of $5, cannot bet $10 even with max confidence
    amount = strategy.calculate_amount(1.0, Decimal("5.00"))
    assert amount == Decimal("0")


def test_strategy_calculate_amount_at_balance():
    """Should allow bet if exactly at balance."""
    strategy = BettingStrategy()
    # With confidence 0.6, amount is $1
    amount = strategy.calculate_amount(0.6, Decimal("1.00"))
    assert amount == Decimal("1.00")


# === Analyzer Tests ===


@pytest.mark.asyncio
async def test_analyzer_parse_valid_response():
    """Should parse valid LLM response into BetDecision."""
    analyzer = GameAnalyzer(api_key="test-key")

    response = """bet: yes
bet_type: side_win
target: citizens
amount: 5.00
confidence: 0.8
reasoning: Citizens have strong momentum"""

    decision = analyzer._parse_response(response)

    assert decision.should_bet is True
    assert decision.bet_type == "side_win"
    assert decision.target == "citizens"
    assert decision.amount_usdc == Decimal("5.00")
    assert decision.confidence == 0.8
    assert "momentum" in decision.reasoning.lower()


@pytest.mark.asyncio
async def test_analyzer_parse_no_bet():
    """Should parse 'no' as should_bet=False."""
    analyzer = GameAnalyzer(api_key="test-key")

    response = """bet: no
bet_type: side_win
target: citizens
amount: 0
confidence: 0.3
reasoning: Not enough information"""

    decision = analyzer._parse_response(response)

    assert decision.should_bet is False
    assert decision.confidence == 0.3


@pytest.mark.asyncio
async def test_analyzer_parse_malformed_returns_no_bet():
    """Should return should_bet=False on malformed response."""
    analyzer = GameAnalyzer(api_key="test-key")

    with patch.object(analyzer, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "This is not a valid format"

        observation = GameObservation(
            game_id="game123",
            phase="day_discussion",
            round_number=1,
            alive_agents=("alice", "bob"),
            dead_agents=(),
            recent_events=(),
            current_odds={},
        )

        decision = await analyzer.analyze_and_decide(observation, Decimal("100.00"))

        # Should handle gracefully
        assert decision.should_bet is False


@pytest.mark.asyncio
async def test_analyzer_api_error_returns_no_bet():
    """Should return should_bet=False on API error."""
    analyzer = GameAnalyzer(api_key="test-key")

    with patch.object(analyzer, "_call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("API error")

        observation = GameObservation(
            game_id="game123",
            phase="day_discussion",
            round_number=1,
            alive_agents=("alice", "bob"),
            dead_agents=(),
            recent_events=(),
            current_odds={},
        )

        decision = await analyzer.analyze_and_decide(observation, Decimal("100.00"))

        assert decision.should_bet is False
        assert "failed" in decision.reasoning.lower()


@pytest.mark.asyncio
async def test_analyzer_build_prompt():
    """Should build proper prompt from observation."""
    analyzer = GameAnalyzer(api_key="test-key")

    observation = GameObservation(
        game_id="game123",
        phase="day_discussion",
        round_number=2,
        alive_agents=("alice", "bob", "charlie"),
        dead_agents=("dave",),
        recent_events=("Round 1 started", "Dave eliminated"),
        current_odds={"alice": Decimal("2.5"), "bob": Decimal("3.0")},
    )

    prompt = analyzer._build_prompt(observation, Decimal("50.00"))

    assert "Phase: day_discussion" in prompt
    assert "Round: 2" in prompt
    assert "alice, bob, charlie" in prompt
    assert "dave" in prompt
    assert "Dave eliminated" in prompt
    assert "50.00 USDC" in prompt


# === Client Tests ===


@pytest.mark.asyncio
async def test_client_build_observation():
    """Should build observation from accumulated events."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    # Simulate game state accumulation
    client.current_game_id = "game123"
    client.current_phase = "day_discussion"
    client.current_round = 2
    client.alive_agents = ["alice", "bob"]
    client.dead_agents = ["charlie"]
    client.recent_events = ["Event 1", "Event 2"]
    client.current_odds = {"alice": Decimal("2.5")}

    observation = client._build_observation()

    assert observation is not None
    assert observation.game_id == "game123"
    assert observation.phase == "day_discussion"
    assert observation.round_number == 2
    assert observation.alive_agents == ("alice", "bob")
    assert observation.dead_agents == ("charlie",)
    assert observation.recent_events == ("Event 1", "Event 2")
    assert observation.current_odds == {"alice": Decimal("2.5")}


@pytest.mark.asyncio
async def test_client_build_observation_no_game():
    """Should return None if no game_id set."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    observation = client._build_observation()
    assert observation is None


@pytest.mark.asyncio
async def test_client_reset_game_state():
    """Should reset accumulated state for new game."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    # Set some state
    client.current_game_id = "old-game"
    client.current_phase = "day_vote"
    client.alive_agents = ["alice"]
    client.recent_events = ["old event"]

    # Reset
    client._reset_game_state("new-game")

    assert client.current_game_id == "new-game"
    assert client.current_phase == "lobby"
    assert client.current_round == 0
    assert client.alive_agents == []
    assert client.dead_agents == []
    assert client.recent_events == []
    assert client.current_odds == {}


@pytest.mark.asyncio
async def test_client_add_event_rolling_window():
    """Should maintain rolling window of last 10 events."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    # Add 15 events
    for i in range(15):
        client._add_event(f"Event {i}")

    # Should only keep last 10
    assert len(client.recent_events) == 10
    assert client.recent_events[0] == "Event 5"
    assert client.recent_events[-1] == "Event 14"


@pytest.mark.asyncio
async def test_client_handle_game_started_event():
    """Should handle game_started event."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    event = {
        "event_type": "game_started",
        "game_id": "game123",
        "data": {
            "phase": "night",
            "alive_agents": ["alice", "bob", "charlie"],
        },
    }

    await client._handle_event(event)

    assert client.current_game_id == "game123"
    assert client.current_phase == "night"
    assert client.alive_agents == ["alice", "bob", "charlie"]
    assert len(client.recent_events) == 1


@pytest.mark.asyncio
async def test_client_handle_elimination_event():
    """Should handle elimination event."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    client.alive_agents = ["alice", "bob", "charlie"]

    event = {
        "event_type": "elimination",
        "game_id": "game123",
        "data": {"agent": "bob"},
    }

    await client._handle_event(event)

    assert "bob" not in client.alive_agents
    assert "bob" in client.dead_agents
    assert any("bob" in e.lower() for e in client.recent_events)


@pytest.mark.asyncio
async def test_client_lifecycle():
    """Should start and stop cleanly."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    assert client._running is False

    # Stop immediately (don't actually run)
    await client.stop()

    assert client._running is False


@pytest.mark.asyncio
async def test_client_place_bet_updates_state():
    """Should update state immutably after successful bet."""
    client = AIBettorClient(
        ws_url="ws://localhost:8080/ws",
        api_url="http://localhost:8080",
        api_key="test-key",
        budget_usdc=Decimal("100.00"),
    )

    # Mock successful API call
    with patch.object(client, "_place_bet_via_api", new_callable=AsyncMock) as mock_bet:
        mock_bet.return_value = True

        # Mock analyzer decision
        with patch.object(
            client.analyzer, "analyze_and_decide", new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = BetDecision(
                should_bet=True,
                bet_type="side_win",
                target="citizens",
                amount_usdc=Decimal("5.00"),  # This is ignored by client
                confidence=0.8,
                reasoning="Test",
            )

            observation = GameObservation(
                game_id="game123",
                phase="day_discussion",
                round_number=1,
                alive_agents=("alice", "bob"),
                dead_agents=(),
                recent_events=(),
                current_odds={},
            )

            initial_balance = client.state.balance_usdc
            initial_bets = client.state.bets_placed

            await client._maybe_place_bet(observation)

            # Calculate expected amount from strategy (confidence 0.8 -> $5.50)
            expected_amount = BettingStrategy.calculate_amount(0.8, initial_balance)

            # State should be updated immutably
            assert client.state.balance_usdc == initial_balance - expected_amount
            assert client.state.bets_placed == initial_bets + 1
            assert client.state.last_bet_time is not None
            assert client.state.total_wagered == expected_amount
