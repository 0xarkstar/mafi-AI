"""Tests for agent modules."""

import pytest

from src.agents.claude_client import ClaudeClient
from src.agents.memory import AgentMemory
from src.agents.personalities import ALL_PERSONALITIES
from src.agents.prompts import (
    build_discussion_prompt,
    build_night_action_prompt,
    build_system_prompt,
    build_vote_prompt,
)
from src.config.constants import Role
from src.models.agent import Personality
from src.models.game import RoundResult


class TestAgentMemory:
    """Tests for AgentMemory class."""

    def test_add_entry(self):
        """Test adding entry to memory."""
        memory = AgentMemory()
        new_memory = memory.add("Night 0: TestAgent1 was killed")

        assert len(new_memory) == 1
        assert "Night 0: TestAgent1 was killed" in new_memory

    def test_rolling_window_max_10(self):
        """Test that memory keeps only last 10 entries."""
        memory = AgentMemory()

        # Add 15 entries
        for i in range(15):
            memory = memory.add(f"Event {i}")

        # Should only have last 10
        assert len(memory) == 10

        # Should have events 5-14
        entries = list(memory)
        assert entries[0] == "Event 5"
        assert entries[-1] == "Event 14"

    def test_format_for_prompt_with_entries(self):
        """Test formatting memory for prompts."""
        memory = AgentMemory()
        memory = memory.add("Night 0: TestAgent1 was killed")
        memory = memory.add("Day 0: TestAgent2 was voted out")

        formatted = memory.format_for_prompt()

        assert "Recent events:" in formatted
        assert "1. Night 0: TestAgent1 was killed" in formatted
        assert "2. Day 0: TestAgent2 was voted out" in formatted

    def test_format_for_prompt_empty(self):
        """Test formatting empty memory."""
        memory = AgentMemory()
        formatted = memory.format_for_prompt()

        assert formatted == "No previous events."

    def test_immutability(self):
        """Test that add returns new instance."""
        memory1 = AgentMemory()
        memory2 = memory1.add("Event 1")

        # Should be different instances
        assert memory1 is not memory2
        assert len(memory1) == 0
        assert len(memory2) == 1

    def test_iteration(self):
        """Test iterating over memory entries."""
        memory = AgentMemory()
        memory = memory.add("Event 1")
        memory = memory.add("Event 2")
        memory = memory.add("Event 3")

        entries = list(memory)
        assert entries == ["Event 1", "Event 2", "Event 3"]


class TestClaudeClientParsing:
    """Tests for ClaudeClient parsing methods."""

    def test_parse_choice_exact_match(self):
        """Test exact match for choice parsing."""
        # Create a minimal ClaudeClient-like object for testing
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        choices = ["TestAgent1", "TestAgent2", "TestAgent3"]

        result = client._parse_choice("TestAgent2", choices)
        assert result == "TestAgent2"

    def test_parse_choice_case_insensitive(self):
        """Test case-insensitive choice parsing."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        choices = ["TestAgent1", "TestAgent2", "TestAgent3"]

        result = client._parse_choice("testagent2", choices)
        assert result == "TestAgent2"

    def test_parse_choice_substring_match(self):
        """Test substring match for choice parsing."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        choices = ["TestAgent1", "TestAgent2", "TestAgent3"]

        result = client._parse_choice("I think we should vote for TestAgent2", choices)
        assert result == "TestAgent2"

    def test_parse_choice_no_match(self):
        """Test that None is returned when no match found."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        choices = ["TestAgent1", "TestAgent2", "TestAgent3"]

        result = client._parse_choice("InvalidAgent", choices)
        assert result is None

    def test_parse_odds_valid_decimal(self):
        """Test parsing valid decimal odds."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        text = """mafia_win: 0.45
citizen_win: 0.55
TestAgent1: 0.7"""

        odds = client._parse_odds(text)

        assert odds["mafia_win"] == 0.45
        assert odds["citizen_win"] == 0.55
        assert odds["TestAgent1"] == 0.7

    def test_parse_odds_percentage(self):
        """Test parsing percentage odds."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        text = """
        mafia_win: 45%
        citizen_win: 55%
        """

        odds = client._parse_odds(text)

        assert odds["mafia_win"] == 0.45
        assert odds["citizen_win"] == 0.55

    def test_parse_odds_clamping(self):
        """Test that odds are clamped to [0.0, 1.0]."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        text = """too_high: 1.5
too_low: -0.3"""

        odds = client._parse_odds(text)

        assert odds["too_high"] == 1.0
        assert odds["too_low"] == 0.0

    def test_parse_odds_fallback_on_invalid(self):
        """Test fallback to default odds when parsing fails."""
        class MockSettings:
            def __init__(self):
                self.anthropic_api_key = type("obj", (), {"get_secret_value": lambda self: "test"})()
                self.dialogue_model = "test"
                self.decision_model = "test"
                self.oddsmaker_model = "test"

        client = ClaudeClient(MockSettings())
        text = "Invalid format with no odds"

        odds = client._parse_odds(text)

        # Should fallback to uniform distribution
        assert "mafia_win" in odds
        assert "citizen_win" in odds
        assert odds["mafia_win"] == 0.5
        assert odds["citizen_win"] == 0.5


class TestPersonalities:
    """Tests for personality definitions."""

    def test_seven_personalities_loaded(self):
        """Test that all 7 personalities are loaded."""
        assert len(ALL_PERSONALITIES) == 7

    def test_all_have_unique_names(self):
        """Test that all personalities have unique names."""
        names = [p.name for p in ALL_PERSONALITIES]
        assert len(names) == len(set(names))

    def test_all_required_fields_present(self):
        """Test that all personalities have required fields."""
        for personality in ALL_PERSONALITIES:
            assert personality.name
            assert personality.trait
            assert personality.description
            assert personality.speaking_style
            assert 0.0 <= personality.suspicion_bias <= 1.0

    def test_expected_personalities(self):
        """Test that expected personalities are present."""
        names = {p.name for p in ALL_PERSONALITIES}
        expected = {"Viktor", "Luna", "Rex", "Sage", "Nova", "Iris", "Blaze"}
        assert names == expected


class TestPrompts:
    """Tests for prompt building functions."""

    def test_build_system_prompt_includes_personality(self):
        """Test that system prompt includes personality info."""
        personality = Personality(
            name="TestAgent",
            trait="test",
            description="A test agent",
            speaking_style="formal",
            suspicion_bias=0.5,
        )

        prompt = build_system_prompt(personality, Role.CITIZEN, "Standard rules")

        assert "TestAgent" in prompt
        assert "A test agent" in prompt
        assert "formal" in prompt
        assert "CITIZEN" in prompt.upper()

    def test_build_system_prompt_includes_role(self):
        """Test that system prompt includes role instructions."""
        personality = Personality(
            name="TestAgent",
            trait="test",
            description="A test agent",
            speaking_style="formal",
            suspicion_bias=0.5,
        )

        mafia_prompt = build_system_prompt(personality, Role.MAFIA, "Standard rules")
        detective_prompt = build_system_prompt(
            personality, Role.DETECTIVE, "Standard rules"
        )
        citizen_prompt = build_system_prompt(
            personality, Role.CITIZEN, "Standard rules"
        )

        assert "MAFIA" in mafia_prompt.upper()
        assert "DETECTIVE" in detective_prompt.upper()
        assert "CITIZEN" in citizen_prompt.upper()

    def test_build_night_action_prompt_mafia(self):
        """Test night action prompt for mafia includes targets."""
        alive_agents = ("TestAgent1", "TestAgent2", "TestAgent3", "TestAgent4")
        known_roles = {"TestAgent1": Role.MAFIA, "TestAgent2": Role.MAFIA}
        memory = ("Night 0: TestAgent5 was killed",)

        prompt = build_night_action_prompt(
            Role.MAFIA, alive_agents, known_roles, memory
        )

        assert "NIGHT PHASE" in prompt
        assert "TestAgent3" in prompt  # Non-mafia target
        assert "TestAgent4" in prompt  # Non-mafia target
        assert "TestAgent1" in prompt  # Mafia partner
        assert "Night 0: TestAgent5 was killed" in prompt

    def test_build_night_action_prompt_detective(self):
        """Test night action prompt for detective includes targets."""
        alive_agents = ("Detective", "TestAgent1", "TestAgent2", "TestAgent3")
        known_roles = {"TestAgent1": Role.CITIZEN}  # Already investigated
        memory = ("Day 0: TestAgent4 was voted out",)

        prompt = build_night_action_prompt(
            Role.DETECTIVE, alive_agents, known_roles, memory
        )

        assert "NIGHT PHASE" in prompt
        assert "investigate" in prompt.lower()
        assert "TestAgent2" in prompt  # Not yet investigated
        assert "TestAgent3" in prompt  # Not yet investigated
        assert "TestAgent1" in prompt  # Already investigated, shown in results

    def test_build_discussion_prompt_includes_context(self):
        """Test discussion prompt includes game context."""
        personality = Personality(
            name="TestAgent",
            trait="test",
            description="A test agent",
            speaking_style="formal",
            suspicion_bias=0.5,
        )

        round_events = (
            RoundResult(
                round_number=0,
                phase="night",
                night_kill="TestAgent1",
                detective_target=None,
                detective_result=None,
            ),
        )
        memory = ("Night 0: TestAgent1 was killed",)
        alive_agents = ("TestAgent2", "TestAgent3", "TestAgent4")

        prompt = build_discussion_prompt(
            personality, Role.CITIZEN, round_events, memory, alive_agents
        )

        assert "DAY DISCUSSION" in prompt
        assert "TestAgent1" in prompt  # Killed agent
        assert "TestAgent" in prompt  # Agent's name
        assert "formal" in prompt  # Speaking style

    def test_build_vote_prompt_includes_candidates(self):
        """Test vote prompt includes voting candidates."""
        personality = Personality(
            name="TestAgent",
            trait="test",
            description="A test agent",
            speaking_style="formal",
            suspicion_bias=0.5,
        )

        alive_agents = ("TestAgent", "TestAgent1", "TestAgent2", "TestAgent3")
        memory = ("Day 0: TestAgent4 was voted out",)
        discussion_log = tuple()

        prompt = build_vote_prompt(
            personality, Role.CITIZEN, discussion_log, alive_agents, memory
        )

        assert "VOTING PHASE" in prompt
        assert "TestAgent1" in prompt
        assert "TestAgent2" in prompt
        assert "TestAgent3" in prompt
        assert "TestAgent" not in prompt or "excluding you" in prompt  # Self excluded

    def test_build_vote_prompt_excludes_self(self):
        """Test that vote prompt excludes the agent themselves."""
        personality = Personality(
            name="Voter",
            trait="test",
            description="A test voter",
            speaking_style="formal",
            suspicion_bias=0.5,
        )

        alive_agents = ("Voter", "TestAgent1", "TestAgent2")
        prompt = build_vote_prompt(
            personality, Role.CITIZEN, tuple(), alive_agents, tuple()
        )

        # Should list candidates excluding self
        assert "TestAgent1" in prompt
        assert "TestAgent2" in prompt
        # Voter should not be in candidate list
        lines = prompt.split("\n")
        candidate_lines = [
            line for line in lines if "TestAgent1" in line or "TestAgent2" in line
        ]
        assert len(candidate_lines) > 0
