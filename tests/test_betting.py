"""Betting module tests - USDC only."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.betting.manager import BettingManager
from src.betting.odds import apply_early_bonus, calculate_implied_odds
from src.betting.oddsmaker import calculate_ai_odds
from src.betting.pool import calculate_payout
from src.config.constants import (
    BetType,
    EARLY_BET_MULTIPLIERS,
    HOUSE_EDGE,
    MAX_BET_USDC,
    MIN_BET_USDC,
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
                bettor_id="0xuser1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("100"),
                round_placed=0,
                weight=Decimal("1.0"),
                tx_hash="0xtx1",
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="0xuser2",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("200"),
                round_placed=0,
                weight=Decimal("1.5"),
                tx_hash="0xtx2",
            ),
            Bet(
                bet_id="bet3",
                game_id="test",
                bettor_id="0xuser3",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
                weight=Decimal("1.0"),
                tx_hash="0xtx3",
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
        assert payouts["0xuser1"] == Decimal("95")
        assert payouts["0xuser2"] == Decimal("285")
        assert "0xuser3" not in payouts

    def test_bet_placement(self):
        """Test placing bets and verifying Bet model fields."""
        bet = Bet(
            bet_id="bet123",
            game_id="game456",
            bettor_id="0xuser789",
            bet_type=BetType.NEXT_ELIMINATION,
            target="Viktor",
            amount=Decimal("50"),
            round_placed=1,
            weight=Decimal("1.2"),
            tx_hash="0xtxhash123",
        )

        # Verify all fields
        assert bet.bet_id == "bet123"
        assert bet.game_id == "game456"
        assert bet.bettor_id == "0xuser789"
        assert bet.bet_type == BetType.NEXT_ELIMINATION
        assert bet.target == "Viktor"
        assert bet.amount == Decimal("50")
        assert bet.round_placed == 1
        assert bet.weight == Decimal("1.2")
        assert bet.tx_hash == "0xtxhash123"

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
                bettor_id="0xuser1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("500"),
                round_placed=0,
                weight=Decimal("1.0"),
                tx_hash="0xtx1",
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="0xuser2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("500"),
                round_placed=0,
                weight=Decimal("1.0"),
                tx_hash="0xtx2",
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
        assert payouts["0xuser1"] == Decimal("950")

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
            bettor_id="0xuser1",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("100"),
            round_placed=0,
            tx_hash="0xtx1",
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
                bettor_id="0xuser1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("100"),
                round_placed=0,
                tx_hash="0xtx1",
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="0xuser2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
                tx_hash="0xtx2",
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
                bettor_id="0xuser1",
                bet_type=BetType.SIDE_WIN,
                target="mafia",
                amount=Decimal("300"),
                round_placed=0,
                tx_hash="0xtx1",
            ),
            Bet(
                bet_id="bet2",
                game_id="test",
                bettor_id="0xuser2",
                bet_type=BetType.SIDE_WIN,
                target="citizens",
                amount=Decimal("100"),
                round_placed=0,
                tx_hash="0xtx2",
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

    def test_place_bet_success(self):
        """Test valid USDC bet returns Bet."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place bet
        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtxhash123",
        )

        # Verify bet created
        assert bet is not None
        assert bet.bettor_id == "0xuser1"
        assert bet.target == "mafia"
        assert bet.amount == Decimal("10.00")
        assert bet.bet_type == BetType.SIDE_WIN
        assert bet.tx_hash == "0xtxhash123"

        # Verify bet added to pool
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("10.00")

    def test_place_bet_min_amount_validation(self):
        """Test bet rejected when below MIN_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Try to bet below minimum
        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("0.50"),  # Below MIN_BET_USDC = 1.0
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is None

        # Verify pool empty
        pool = manager.pools[BetType.SIDE_WIN]
        assert len(pool.bets) == 0

    def test_place_bet_max_amount_validation(self):
        """Test bet rejected when above MAX_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Try to bet above maximum
        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("150.00"),  # Above MAX_BET_USDC = 100.0
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is None

    def test_place_bet_exactly_min_amount(self):
        """Test bet accepted at exactly MIN_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=MIN_BET_USDC,
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is not None
        assert bet.amount == MIN_BET_USDC

    def test_place_bet_exactly_max_amount(self):
        """Test bet accepted at exactly MAX_BET_USDC."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=MAX_BET_USDC,
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is not None
        assert bet.amount == MAX_BET_USDC

    def test_place_bet_invalid_type(self):
        """Test bet returns None for bad bet_type."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="invalid_type",
            target="mafia",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is None

    def test_settle_returns_wallet_addresses(self):
        """Test that settle returns dict of wallet_address → payout."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place bets
        manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx1",
        )
        manager.place_bet(
            bettor_address="0xuser2",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx2",
        )

        # Settle with mafia winning
        payouts = manager.settle("mafia")

        # Verify wallet addresses in payouts (not session IDs)
        assert "0xuser1" in payouts
        assert payouts["0xuser1"] == Decimal("19.00")  # 20 pool - 5% edge = 19

        # user2 gets nothing
        assert "0xuser2" not in payouts

    @pytest.mark.asyncio
    async def test_update_odds_blending(self):
        """Test that update_odds blends AI odds with market odds (70/30)."""
        mock_claude = MagicMock()
        mock_claude.analyze_odds = AsyncMock(
            return_value={"mafia_win": 0.5, "citizen_win": 0.5}
        )

        manager = BettingManager(mock_claude, "test-game")

        # Place bets to create market odds: 60% mafia, 40% citizens
        manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("6.00"),
            round_number=0,
            tx_hash="0xtx1",
        )
        manager.place_bet(
            bettor_address="0xuser2",
            bet_type="side_win",
            target="citizens",
            amount_usdc=Decimal("4.00"),
            round_number=0,
            tx_hash="0xtx2",
        )

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

        # Place bet on Viktor being AI
        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="is_ai_or_human",
            target="Viktor:ai",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx",
        )

        assert bet is not None
        assert bet.bet_type == BetType.IS_AI_OR_HUMAN
        assert bet.target == "Viktor:ai"
        assert bet.amount == Decimal("10.00")

        # Verify pool updated
        pool = manager.pools[BetType.IS_AI_OR_HUMAN]
        assert len(pool.bets) == 1
        assert pool.total_amount == Decimal("10.00")

    def test_settle_identity_bets_returns_wallet_addresses(self):
        """Test settling identity bets returns wallet addresses."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place bets
        manager.place_bet(
            bettor_address="0xuser1",
            bet_type="is_ai_or_human",
            target="Viktor:ai",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx1",
        )
        manager.place_bet(
            bettor_address="0xuser2",
            bet_type="is_ai_or_human",
            target="Viktor:human",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx2",
        )

        # Create mock player Viktor who is AI
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        players = {"Viktor": mock_viktor}

        # Settle bets
        payouts = manager.settle_identity_bets(players)

        # Verify wallet addresses in payouts
        assert "0xuser1" in payouts  # Won (bet AI, Viktor is AI)
        assert payouts["0xuser1"] == Decimal("19.00")  # 20 pool - 5% = 19
        assert "0xuser2" not in payouts  # Lost

    def test_settle_identity_bets_multiple_winners(self):
        """Test settling identity bets with multiple winners."""
        from src.config.constants import PlayerType

        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        # Place bets
        manager.place_bet(
            bettor_address="0xuser1",
            bet_type="is_ai_or_human",
            target="Viktor:ai",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx1",
        )
        manager.place_bet(
            bettor_address="0xuser2",
            bet_type="is_ai_or_human",
            target="Viktor:human",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx2",
        )
        manager.place_bet(
            bettor_address="0xuser3",
            bet_type="is_ai_or_human",
            target="Luna:human",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx3",
        )

        # Create mock players
        mock_viktor = MagicMock()
        mock_viktor.player_type = PlayerType.HOUSE_AI

        mock_luna = MagicMock()
        mock_luna.player_type = PlayerType.AGENT_HUMAN

        players = {"Viktor": mock_viktor, "Luna": mock_luna}

        # Settle bets
        payouts = manager.settle_identity_bets(players)

        # user1 and user3 win
        # Total pool: 30, house edge: 5%, net: 28.5
        # Winning bets: user1 (10 * 1.5 = 15), user3 (10 * 1.5 = 15)
        # Total winning weight: 30
        # user1 gets: (15/30) * 28.5 = 14.25
        # user3 gets: (15/30) * 28.5 = 14.25

        assert "0xuser1" in payouts
        assert "0xuser3" in payouts
        assert "0xuser2" not in payouts

        assert payouts["0xuser1"] == Decimal("14.25")
        assert payouts["0xuser3"] == Decimal("14.25")

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

    def test_reset_clears_pools(self):
        """Test reset empties all betting pools."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "game-1")

        # Place a bet in the pool
        manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            tx_hash="0xtx1",
        )

        # Verify bet was placed
        assert len(manager.pools[BetType.SIDE_WIN].bets) == 1

        # Reset with a new game id
        manager.reset("game-2")

        # All pools should be empty after reset
        for pool in manager.pools.values():
            assert len(pool.bets) == 0
            assert pool.total_amount == Decimal("0")

    def test_reset_updates_game_id(self):
        """Test reset updates game_id to the new value."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "game-1")
        assert manager.game_id == "game-1"

        manager.reset("game-2")

        assert manager.game_id == "game-2"

    def test_reset_clears_odds(self):
        """Test reset sets odds_board to None."""
        from unittest.mock import AsyncMock
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "game-1")
        # Manually set odds_board to something non-None
        manager.odds_board = MagicMock()

        manager.reset("game-2")

        assert manager.odds_board is None

    def test_place_bet_without_tx_hash(self):
        """Test placing a bet works when tx_hash is None."""
        mock_claude = MagicMock()
        manager = BettingManager(mock_claude, "test-game")

        bet = manager.place_bet(
            bettor_address="0xuser1",
            bet_type="side_win",
            target="mafia",
            amount_usdc=Decimal("10.00"),
            round_number=0,
            # tx_hash intentionally omitted (defaults to None)
        )

        assert bet is not None
        assert bet.tx_hash is None

    def test_bet_model_tx_hash_optional(self):
        """Test Bet model can be created without tx_hash."""
        bet = Bet(
            bet_id="bet1",
            game_id="game1",
            bettor_id="0xuser1",
            bet_type=BetType.SIDE_WIN,
            target="mafia",
            amount=Decimal("10.00"),
            round_placed=0,
        )

        assert bet.tx_hash is None
