"""Betting module tests - to be implemented with betting module."""

import pytest


class TestBettingPool:
    """Tests for betting pool - placeholder until betting module is implemented."""

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_pari_mutuel_payout(self):
        """Test pari-mutuel payout calculation."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_bet_placement(self):
        """Test placing bets on outcomes."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_house_edge_calculation(self):
        """Test that house edge is applied correctly."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_early_bet_multipliers(self):
        """Test early bet multipliers for rounds 0 and 1."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_bet_window_timeout(self):
        """Test that betting window closes after timeout."""
        pass


class TestOddsmaker:
    """Tests for oddsmaker - placeholder until betting module is implemented."""

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_odds_calculation(self):
        """Test odds calculation based on game state."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_odds_update_on_elimination(self):
        """Test that odds update when agent is eliminated."""
        pass

    @pytest.mark.skip(reason="Betting module not yet implemented")
    def test_odds_broadcast_to_spectators(self):
        """Test that odds are broadcast via WebSocket."""
        pass
