"""Betting module tests."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.betting.manager import BettingManager
from src.betting.odds import apply_early_bonus, calculate_implied_odds
from src.betting.oddsmaker import calculate_ai_odds
from src.betting.pool import calculate_payout
from src.config.constants import (
    BetType,
    DEFAULT_STARTING_CHIPS,
    EARLY_BET_MULTIPLIERS,
    HOUSE_EDGE,
    Phase,
    Role,
)
from src.models.betting import Bet, BettingPool, OddsBoard


class TestBettingPool:
    """Tests for betting pool payout calculations."""

    def test_pari_mutuel_payout(self):
        """Test pari-mutuel payout calculation with 3 bets on different targets."""
        # Create bets: 100 on mafia (weight 1.0), 200 on mafia (weight 1.5), 100 on citizens
        bets = (
            Bet(
                bet_id="bet1",
                game_id="test",
                bettor_id="user1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("100"),
                round_placed=0,
                weight=Decimal("1.0"),
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="user2",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("200"),
                round_placed=0,
                weight=Decimal("1.5"),
            ),
            Bet(
                bet_id="bet3",
                game_id="test",
                bettor_id="user3",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
                weight=Decimal("1.0"),
            ),
        )

        pool = BettingPool(
            game_id="test",
            bet_type=BetType.SIDE_WIN,
            bets=bets,
            total_amount=Decimal("400"),
        )

        # Mafia wins
        payouts = calculate_payout(pool, "mafia")

        # Total pool: 400, house edge: 5%, net: 380
        # Winning bets: bet1 (100 * 1.0 = 100 weighted), bet2 (200 * 1.5 = 300 weighted)
        # Total weighted: 400
        # user1 payout: (100/400) * 380 = 95
        # user2 payout: (300/400) * 380 = 285

        assert len(payouts) == 2
        assert payouts["user1"] == Decimal("95")
        assert payouts["user2"] == Decimal("285")
        assert "user3" not in payouts

    def test_bet_placement(self):
        """Test placing bets and verifying Bet model fields."""
        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="user789",
            bet_type=BetType.NEXT_ELIMINATION,
            target="Viktor",
            amount=Decimal("50"),
            round_placed=1,
            weight=Decimal("1.2"),
        )

        # Verify all fields
        assert bet.bet_id == "bet123"
        assert bet.game_id == "game456"
        assert bet.bettor_id == "user789"
        assert bet.bet_type == BetType.NEXT_ELIMINATION
        assert bet.target == "Viktor"
        assert bet.amount == Decimal("50")
        assert bet.round_placed == 1
        assert bet.weight == Decimal("1.2")

        # Test pool total updates
        pool = BettingPool(game_id="game456", bet_type=BetType.NEXT_ELIMINATION)
        assert pool.total_amount == Decimal("0")
        assert len(pool.bets) == 0

        # Add bet to pool (immutably)
        new_pool = pool.model_copy(
            update={
                "bets": pool.bets + (bet,),
                "total_amount": pool.total_amount + bet.amount,
            }
        )

        assert new_pool.total_amount == Decimal("50")
        assert len(new_pool.bets) == 1
        assert new_pool.bets[0] == bet

    def test_house_edge_calculation(self):
        """Test that 95% goes to winners, 5% house cut."""
        # Create 1000 total pool, mafia wins
        bets = (
            Bet(
                bet_id="bet1",
                game_id="test",
                bettor_id="user1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("500"),
                round_placed=0,
                weight=Decimal("1.0"),
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="user2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("500"),
                round_placed=0,
                weight=Decimal("1.0"),
            ),
        )

        pool = BettingPool(
            game_id="test",
            bet_type=BetType.SIDE_WIN,
            bets=bets,
            total_amount=Decimal("1000"),
        )

        payouts = calculate_payout(pool, "mafia")

        # Total: 1000, house edge: 5% (50), net: 950
        # user1 gets all 950 (only winner)
        assert payouts["user1"] == Decimal("950")

        # Verify house edge is exactly 5%
        total_paid_out = sum(payouts.values())
        house_take = Decimal("1000") - total_paid_out
        assert house_take == Decimal("50")
        assert house_take / Decimal("1000") == Decimal(str(HOUSE_EDGE))

    def test_early_bet_multipliers(self):
        """Test early bet multipliers: Round 0 → 1.5x, Round 1 → 1.2x, Round 2+ → 1.0x."""
        base_bet = Bet(
            bet_id="bet1",
            game_id="test",
            bettor_id="user1",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("100"),
            round_placed=0,
        )

        # Round 0: 1.5x
        bet_r0 = apply_early_bonus(base_bet, 0)
        assert bet_r0.weight == Decimal(str(EARLY_BET_MULTIPLIERS[0]))
        assert bet_r0.weight == Decimal("1.5")

        # Round 1: 1.2x
        bet_r1 = apply_early_bonus(base_bet, 1)
        assert bet_r1.weight == Decimal(str(EARLY_BET_MULTIPLIERS[1]))
        assert bet_r1.weight == Decimal("1.2")

        # Round 2+: 1.0x (default)
        bet_r2 = apply_early_bonus(base_bet, 2)
        assert bet_r2.weight == Decimal("1.0")

        bet_r5 = apply_early_bonus(base_bet, 5)
        assert bet_r5.weight == Decimal("1.0")

        # Verify immutability
        assert base_bet.weight == Decimal("1.0")  # Original unchanged

    def test_bet_window_timeout(self):
        """Test bet rejection for invalid amounts (0, negative, exceeds balance)."""
        # This test verifies BettingManager validation
        mock_claude = MagicMock()
        mock_claude.analyze_odds = AsyncMock(
            return_value={"mafia_win": 0.5, "citizen_win": 0.5}
        )

        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=100)

        # Test zero amount
        bet = manager.place_bet("user1", "side_win", "mafia", 0, 0)
        assert bet is None

        # Test negative amount
        bet = manager.place_bet("user1", "side_win", "mafia", -50, 0)
        assert bet is None

        # Test exceeds balance
        bet = manager.place_bet("user1", "side_win", "mafia", 200, 0)
        assert bet is None

        # Test valid bet
        bet = manager.place_bet("user1", "side_win", "mafia", 50, 0)
        assert bet is not None
        assert bet.amount == Decimal("50")


class TestOddsmaker:
    """Tests for AI odds calculation."""

    @pytest.mark.asyncio
    async def test_odds_calculation(self):
        """Test odds calculation with mocked Claude response."""
        # Create mock Claude client
        mock_claude = MagicMock()
        mock_claude.analyze_odds = AsyncMock(
            return_value={
                "mafia_win": 0.4,
                "citizen_win": 0.6,
                "Viktor": 0.7,
                "Luna": 0.3,
            }
        )

        # Create sample game state
        from src.models.game import GameState

        game_state = GameState(
            game_id="test-game",
            phase=Phase.DAY_DISCUSSION,
            round_number=1,
            alive_agents=("Viktor", "Luna", "Rex"),
            dead_agents=("Sage",),
            role_map={
                "Viktor": Role.MAFIA,
                "Luna": Role.DETECTIVE,
                "Rex": Role.CITIZEN,
                "Sage": Role.CITIZEN,
            },
            rounds=tuple(),
            winner=None,
        )

        # Calculate AI odds
        odds_board = await calculate_ai_odds(game_state, mock_claude)

        # Verify OddsBoard structure
        assert odds_board.game_id == "test-game"
        assert odds_board.round_number == 1
        assert odds_board.mafia_win_prob == Decimal("0.4")
        assert odds_board.citizen_win_prob == Decimal("0.6")

        # Verify mafia suspects
        assert "Viktor" in odds_board.mafia_suspects
        assert "Luna" in odds_board.mafia_suspects
        assert odds_board.mafia_suspects["Viktor"] == Decimal("0.7")
        assert odds_board.mafia_suspects["Luna"] == Decimal("0.3")

        # Verify probabilities are valid (0-1)
        assert 0 <= odds_board.mafia_win_prob <= 1
        assert 0 <= odds_board.citizen_win_prob <= 1

    @pytest.mark.asyncio
    async def test_odds_update_on_elimination(self):
        """Test that odds change when game state has fewer alive agents."""
        mock_claude = MagicMock()

        # First call: 4 agents alive
        mock_claude.analyze_odds = AsyncMock(
            return_value={
                "mafia_win": 0.5,
                "citizen_win": 0.5,
                "Viktor": 0.25,
                "Luna": 0.25,
                "Rex": 0.25,
                "Sage": 0.25,
            }
        )

        from src.models.game import GameState

        state1 = GameState(
            game_id="test-game",
            phase=Phase.DAY_DISCUSSION,
            round_number=0,
            alive_agents=("Viktor", "Luna", "Rex", "Sage"),
            dead_agents=tuple(),
            role_map={
                "Viktor": Role.MAFIA,
                "Luna": Role.DETECTIVE,
                "Rex": Role.CITIZEN,
                "Sage": Role.CITIZEN,
            },
            rounds=tuple(),
            winner=None,
        )

        odds1 = await calculate_ai_odds(state1, mock_claude)
        assert len(odds1.mafia_suspects) == 4

        # Second call: 3 agents alive (Sage eliminated)
        mock_claude.analyze_odds = AsyncMock(
            return_value={
                "mafia_win": 0.6,
                "citizen_win": 0.4,
                "Viktor": 0.5,
                "Luna": 0.3,
                "Rex": 0.2,
            }
        )

        state2 = GameState(
            game_id="test-game",
            phase=Phase.DAY_DISCUSSION,
            round_number=1,
            alive_agents=("Viktor", "Luna", "Rex"),
            dead_agents=("Sage",),
            role_map=state1.role_map,
            rounds=tuple(),
            winner=None,
        )

        odds2 = await calculate_ai_odds(state2, mock_claude)
        assert len(odds2.mafia_suspects) == 3
        assert "Sage" not in odds2.mafia_suspects

        # Verify odds changed
        assert odds2.mafia_win_prob != odds1.mafia_win_prob
        assert odds2.round_number == 1

    @pytest.mark.asyncio
    async def test_odds_broadcast_to_spectators(self):
        """Test that BettingManager.update_odds returns OddsBoard."""
        mock_claude = MagicMock()
        mock_claude.analyze_odds = AsyncMock(
            return_value={"mafia_win": 0.45, "citizen_win": 0.55}
        )

        manager = BettingManager(mock_claude, "test-game")

        from src.models.game import GameState

        game_state = GameState(
            game_id="test-game",
            phase=Phase.NIGHT,
            round_number=0,
            alive_agents=("Viktor", "Luna"),
            dead_agents=tuple(),
            role_map={"Viktor": Role.MAFIA, "Luna": Role.CITIZEN},
            rounds=tuple(),
            winner=None,
        )

        # Update odds
        odds_board = await manager.update_odds(game_state)

        # Verify OddsBoard returned
        assert isinstance(odds_board, OddsBoard)
        assert odds_board.game_id == "test-game"
        assert odds_board.round_number == 0

        # Verify manager stored the board
        assert manager.odds_board is not None
        assert manager.odds_board == odds_board


class TestImpliedOdds:
    """Tests for implied odds calculation from bet distribution."""

    def test_calculate_implied_odds_uniform(self):
        """Test implied odds with equal bets on two targets."""
        bets = (
            Bet(
                bet_id="bet1",
                game_id="test",
                bettor_id="user1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("100"),
                round_placed=0,
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="user2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
            ),
        )

        pool = BettingPool(game_id="test", bet_type=BetType.SIDE_WIN, bets=bets)

        implied = calculate_implied_odds(pool)

        assert implied["mafia"] == Decimal("0.5")
        assert implied["citizens"] == Decimal("0.5")

    def test_calculate_implied_odds_skewed(self):
        """Test implied odds with skewed bet distribution."""
        bets = (
            Bet(
                bet_id="bet1",
                game_id="test",
                bettor_id="user1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("300"),
                round_placed=0,
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="user2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
            ),
        )

        pool = BettingPool(game_id="test", bet_type=BetType.SIDE_WIN, bets=bets)

        implied = calculate_implied_odds(pool)

        # 300/400 = 0.75, 100/400 = 0.25
        assert implied["mafia"] == Decimal("0.75")
        assert implied["citizens"] == Decimal("0.25")

    def test_calculate_implied_odds_empty_pool(self):
        """Test implied odds with no bets."""
        pool = BettingPool(game_id="test", bet_type=BetType.SIDE_WIN, bets=tuple())

        implied = calculate_implied_odds(pool)

        assert implied == {}


class TestBettingManager:
    """Tests for BettingManager class."""

    def test_register_spectator(self):
        """Test new spectator gets DEFAULT_STARTING_CHIPS."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register with default chips
        manager.register_spectator("user1")
        assert manager.spectators["user1"] == Decimal(str(DEFAULT_STARTING_CHIPS))

        # Register with custom chips
        manager.register_spectator("user2", chips=500)
        assert manager.spectators["user2"] == Decimal("500")

        # Re-registering doesn't reset chips
        manager.spectators["user1"] = Decimal("750")
        manager.register_spectator("user1")
        assert manager.spectators["user1"] == Decimal("750")

    def test_place_bet_success(self):
        """Test valid bet returns Bet and deducts from balance."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=1000)

        initial_balance = manager.spectators["user1"]

        # Place bet
        bet = manager.place_bet("user1", "side_win", "mafia", 100, 0)

        # Verify bet created
        assert bet is not None
        assert bet.bettor_id == "user1"
        assert bet.target == "mafia"
        assert bet.amount == Decimal("100")
        assert bet.bet_type == BetType.SIDE_WIN

        # Verify balance deducted
        assert manager.spectators["user1"] == initial_balance - Decimal("100")
        assert manager.spectators["user1"] == Decimal("900")

        # Verify bet added to pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("100")

    def test_place_bet_insufficient_chips(self):
        """Test bet returns None when amount > balance."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=50)

        bet = manager.place_bet("user1", "side_win", "mafia", 100, 0)

        assert bet is None
        assert manager.spectators["user1"] == Decimal("50")  # Balance unchanged

    def test_place_bet_invalid_type(self):
        """Test bet returns None for bad bet_type."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=1000)

        bet = manager.place_bet("user1", "invalid_type", "mafia", 100, 0)

        assert bet is None
        assert manager.spectators["user1"] == Decimal("1000")  # Balance unchanged

    def test_place_bet_zero_amount(self):
        """Test bet returns None for amount <= 0."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=1000)

        # Zero amount
        bet = manager.place_bet("user1", "side_win", "mafia", 0, 0)
        assert bet is None

        # Negative amount
        bet = manager.place_bet("user1", "side_win", "mafia", -50, 0)
        assert bet is None

    def test_settle_distributes_payouts(self):
        """Test that settle adds payout to winner balances."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register and place bets
        manager.register_spectator("user1", chips=1000)
        manager.register_spectator("user2", chips=1000)

        manager.place_bet("user1", "side_win", "mafia", 100, 0)
        manager.place_bet("user2", "side_win", "citizens", 100, 0)

        # User balances: user1=900, user2=900

        # Settle with mafia winning
        payouts = manager.settle("mafia")

        # user1 wins: 200 total pool, 5% house edge = 190 net, user1 gets all 190
        assert "user1" in payouts
        assert payouts["user1"] == Decimal("190")

        # Verify balance updated
        assert manager.spectators["user1"] == Decimal("900") + Decimal("190")
        assert manager.spectators["user1"] == Decimal("1090")

        # user2 gets nothing
        assert "user2" not in payouts
        assert manager.spectators["user2"] == Decimal("900")

    def test_get_spectator_balance_auto_registers(self):
        """Test that unknown session_id auto-registers."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Get balance for unregistered user
        balance = manager.get_spectator_balance("new_user")

        # Should auto-register with default chips
        assert balance == Decimal(str(DEFAULT_STARTING_CHIPS))
        assert "new_user" in manager.spectators

    @pytest.mark.asyncio
    async def test_update_odds_blending(self):
        """Test that update_odds blends AI odds with market odds (70/30)."""
        mock_claude = MagicMock()
        mock_claude.analyze_odds = AsyncMock(
            return_value={"mafia_win": 0.5, "citizen_win": 0.5}
        )

        manager = BettingManager(mock_claude, "test-game")

        # Place bets to create market odds: 60% mafia, 40% citizens
        manager.register_spectator("user1", chips=1000)
        manager.register_spectator("user2", chips=1000)
        manager.place_bet("user1", "side_win", "mafia", 60, 0)
        manager.place_bet("user2", "side_win", "citizens", 40, 0)

        from src.models.game import GameState

        game_state = GameState(
            game_id="test-game",
            phase=Phase.NIGHT,
            round_number=0,
            alive_agents=("Viktor", "Luna"),
            dead_agents=tuple(),
            role_map={"Viktor": Role.MAFIA, "Luna": Role.CITIZEN},
            rounds=tuple(),
            winner=None,
        )

        # Update odds
        odds_board = await manager.update_odds(game_state)

        # AI: mafia=0.5, citizens=0.5
        # Market: mafia=0.6, citizens=0.4
        # Blended (70/30): mafia = 0.5*0.7 + 0.6*0.3 = 0.35 + 0.18 = 0.53
        # Blended (70/30): citizens = 0.5*0.7 + 0.4*0.3 = 0.35 + 0.12 = 0.47
        # After normalization (sum=1.0): mafia=0.53, citizens=0.47

        # Allow small floating point tolerance
        mafia_prob = float(odds_board.mafia_win_prob)
        citizen_prob = float(odds_board.citizen_win_prob)

        assert abs(mafia_prob - 0.53) < 0.01
        assert abs(citizen_prob - 0.47) < 0.01

        # Verify sum is 1.0
        assert abs(mafia_prob + citizen_prob - 1.0) < 0.001


class TestIdentityBetting:
    """Tests for identity betting (IS_AI_OR_HUMAN)."""

    def test_identity_bet_pool_exists(self):
        """Test that IS_AI_OR_HUMAN pool is initialized."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        assert BetType.IS_AI_OR_HUMAN in manager.pools
        pool = manager.pools[BetType.IS_AI_OR_HUMAN]
        assert pool.bet_type == BetType.IS_AI_OR_HUMAN
        assert len(pool.bets) == 0

    def test_place_identity_bet(self):
        """Test placing an identity bet."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")
        manager.register_spectator("user1", chips=1000)

        # Place bet on Viktor being AI
        bet = manager.place_bet("user1", "is_ai_or_human", "Viktor", 100, 0)

        assert bet is not None
        assert bet.bet_type == BetType.IS_AI_OR_HUMAN
        assert bet.target == "Viktor"
        assert bet.amount == Decimal("100")

        # Verify pool updated
        pool = manager.pools[BetType.IS_AI_OR_HUMAN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("100")

    def test_settle_identity_bets_ai_correct(self):
        """Test settling identity bets when AI prediction is correct."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register spectators
        manager.register_spectator("user1", chips=1000)
        manager.register_spectator("user2", chips=1000)

        # Place bets: user1 bets Viktor is AI (correct), user2 bets Viktor is human (wrong)
        manager.place_bet("user1", "is_ai_or_human", "Viktor:ai", 100, 0)
        manager.place_bet("user2", "is_ai_or_human", "Viktor:human", 100, 0)

        # Create mock player Viktor who is AI
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        players = {"Viktor": mock_viktor}

        # Settle bets
        payouts = manager.settle_identity_bets(players)

        # user1 should win (bet Viktor is AI, and Viktor IS AI)
        # Total pool: 200, house edge: 5%, net: 190
        # user1 gets all 190
        assert "user1" in payouts
        assert payouts["user1"] == Decimal("190")
        assert "user2" not in payouts

        # Check balances updated
        assert manager.spectators["user1"] == Decimal("900") + Decimal("190")
        assert manager.spectators["user1"] == Decimal("1090")
        assert manager.spectators["user2"] == Decimal("900")  # Lost bet, no payout

    def test_settle_identity_bets_human_correct(self):
        """Test settling identity bets when human prediction is correct."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register spectators
        manager.register_spectator("user1", chips=1000)
        manager.register_spectator("user2", chips=1000)

        # Place bets: user1 bets Luna is human (correct), user2 bets Luna is AI (wrong)
        manager.place_bet("user1", "is_ai_or_human", "Luna:human", 100, 0)
        manager.place_bet("user2", "is_ai_or_human", "Luna:ai", 100, 0)

        # Create mock player Luna who is human
        mock_luna = MagicMock()
        mock_luna.player_type = PlayerType.HUMAN

        players = {"Luna": mock_luna}

        # Settle bets
        payouts = manager.settle_identity_bets(players)

        # user1 should win
        assert "user1" in payouts
        assert payouts["user1"] == Decimal("190")
        assert "user2" not in payouts

    def test_settle_identity_bets_multiple_players(self):
        """Test settling identity bets with multiple players."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Register spectators
        manager.register_spectator("user1", chips=1000)
        manager.register_spectator("user2", chips=1000)
        manager.register_spectator("user3", chips=1000)

        # Place bets:
        # user1 bets Viktor is AI (correct), 100 chips
        # user2 bets Viktor is human (wrong), 100 chips
        # user3 bets Luna is human (correct), 100 chips
        manager.place_bet("user1", "is_ai_or_human", "Viktor:ai", 100, 0)
        manager.place_bet("user2", "is_ai_or_human", "Viktor:human", 100, 0)
        manager.place_bet("user3", "is_ai_or_human", "Luna:human", 100, 0)

        # Create mock players
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        mock_luna = MagicMock()
        mock_luna.player_type = PlayerType.AGENT_HUMAN

        players = {"Viktor": mock_viktor, "Luna": mock_luna}

        # Settle bets
        payouts = manager.settle_identity_bets(players)

        # user1 and user3 win
        # Total pool: 300, house edge: 5%, net: 285
        # Winning bets: user1 (100 * 1.5 = 150 weighted), user3 (100 * 1.5 = 150 weighted)
        # Total winning weight: 300
        # user1 gets: (150/300) * 285 = 142.5
        # user3 gets: (150/300) * 285 = 142.5

        assert "user1" in payouts
        assert "user3" in payouts
        assert "user2" not in payouts

        assert payouts["user1"] == Decimal("142.5")
        assert payouts["user3"] == Decimal("142.5")

    def test_settle_identity_bets_no_bets(self):
        """Test settling identity bets when no bets placed."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Create mock player
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        players = {"Viktor": mock_viktor}

        # Settle bets (no bets placed)
        payouts = manager.settle_identity_bets(players)

        assert payouts == {}

    def test_settle_identity_bets_invalid_format(self):
        """Test settling identity bets with invalid target format."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        manager.register_spectator("user1", chips=1000)

        # Manually create a bet with invalid target format
        from src.models.betting import Bet
        from uuid import uuid4

        invalid_bet = Bet(
            bet_id=str(uuid4()),
            game_id="test-game",
            bettor_id="user1",
            bet_type=BetType.IS_AI_OR_HUMAN,
            target="Viktor",  # Invalid: should be "Viktor:ai" or "Viktor:human"
            amount=Decimal("100"),
            round_placed=0,
        )

        # Add to pool manually
        pool = manager.pools[BetType.IS_AI_OR_HUMAN]
        manager.pools[BetType.IS_AI_OR_HUMAN] = pool.model_copy(
            update={
                "bets": pool.bets + (invalid_bet,),
                "total_amount": pool.total_amount + invalid_bet.amount,
            }
        )

        # Deduct from spectator balance
        manager.spectators["user1"] -= invalid_bet.amount

        # Create mock player
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        players = {"Viktor": mock_viktor}

        # Settle bets (invalid bet should be skipped)
        payouts = manager.settle_identity_bets(players)

        # No payouts because bet was invalid
        assert payouts == {}
