"""Tests for LLMClient._parse_choice and _parse_odds."""

import pytest
from unittest.mock import MagicMock, patch

from src.agents.llm_client import LLMClient


@pytest.fixture
def client():
    settings = MagicMock()
    settings.openai_api_key.get_secret_value.return_value = "sk-test"
    settings.dialogue_model = "gpt-4o-mini"
    settings.decision_model = "gpt-4o-mini"
    settings.oddsmaker_model = "gpt-4o-mini"
    with patch("src.agents.llm_client.openai.AsyncOpenAI"):
        return LLMClient(settings)


class TestParseChoice:
    def test_exact_match(self, client):
        assert client._parse_choice("Alice", ["Alice", "Bob"]) == "Alice"

    def test_exact_match_case_insensitive(self, client):
        assert client._parse_choice("alice", ["Alice", "Bob"]) == "Alice"

    def test_substring_match(self, client):
        assert client._parse_choice("I think Alice did it", ["Alice", "Bob"]) == "Alice"

    def test_substring_match_partial_name(self, client):
        # Substring match runs before word boundary: "Bob" in "Bobbie" matches
        assert client._parse_choice("Bobbie is suspicious", ["Bob", "Alice"]) == "Bob"

    def test_word_boundary_exact_word(self, client):
        assert client._parse_choice("I vote Bob out", ["Bob", "Alice"]) == "Bob"

    def test_no_match_returns_none(self, client):
        assert client._parse_choice("I don't know", ["Alice", "Bob"]) is None

    def test_first_match_wins(self, client):
        # Both Alice and Bob appear; Alice is first in choices list
        result = client._parse_choice("Alice and Bob", ["Alice", "Bob"])
        assert result == "Alice"

    def test_empty_text(self, client):
        assert client._parse_choice("", ["Alice", "Bob"]) is None

    def test_empty_choices(self, client):
        assert client._parse_choice("Alice", []) is None


class TestParseOdds:
    def test_valid_odds_parsing(self, client):
        text = "mafia_win: 0.3\ncitizen_win: 0.7\nAlice: 0.4"
        odds = client._parse_odds(text)
        assert odds["mafia_win"] == pytest.approx(0.3)
        assert odds["citizen_win"] == pytest.approx(0.7)
        assert odds["Alice"] == pytest.approx(0.4)

    def test_percentage_format(self, client):
        text = "mafia_win: 30%\ncitizen_win: 70%"
        odds = client._parse_odds(text)
        assert odds["mafia_win"] == pytest.approx(0.3)
        assert odds["citizen_win"] == pytest.approx(0.7)

    def test_clamping_above_one(self, client):
        text = "mafia_win: 1.5\ncitizen_win: 0.5"
        odds = client._parse_odds(text)
        assert odds["mafia_win"] == pytest.approx(1.0)

    def test_clamping_below_zero(self, client):
        text = "mafia_win: -0.2\ncitizen_win: 0.8"
        odds = client._parse_odds(text)
        assert odds["mafia_win"] == pytest.approx(0.0)

    def test_empty_text_returns_uniform(self, client):
        odds = client._parse_odds("")
        assert odds["mafia_win"] == pytest.approx(0.5)
        assert odds["citizen_win"] == pytest.approx(0.5)

    def test_missing_required_keys_filled_in(self, client):
        # Only agent odds, no mafia_win/citizen_win
        text = "Alice: 0.4\nBob: 0.3"
        odds = client._parse_odds(text)
        assert "mafia_win" in odds
        assert "citizen_win" in odds
        assert odds["mafia_win"] == pytest.approx(0.5)
        assert odds["citizen_win"] == pytest.approx(0.5)

    def test_missing_citizen_win_filled_in(self, client):
        text = "mafia_win: 0.4\nAlice: 0.3"
        odds = client._parse_odds(text)
        assert "citizen_win" in odds
        assert odds["citizen_win"] == pytest.approx(0.5)

    def test_missing_mafia_win_filled_in(self, client):
        text = "citizen_win: 0.6\nAlice: 0.3"
        odds = client._parse_odds(text)
        assert "mafia_win" in odds
        assert odds["mafia_win"] == pytest.approx(0.5)
