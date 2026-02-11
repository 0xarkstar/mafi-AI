"""Claude API client wrapper with retry logic."""

import random
import re

import anthropic

from src.config.settings import Settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry

log = get_logger(__name__)


class ClaudeClient:
    """Wrapper for Claude API with dialogue and decision generation."""

    def __init__(self, settings: Settings):
        """Initialize Claude client.

        Args:
            settings: Application settings with API key and model config.
        """
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )
        self.dialogue_model = settings.dialogue_model
        self.decision_model = settings.decision_model
        self.oddsmaker_model = settings.oddsmaker_model

    @async_retry(max_attempts=3)
    async def generate_dialogue(self, system: str, prompt: str) -> str:
        """Generate dialogue using Haiku model.

        Args:
            system: System prompt with personality and role.
            prompt: User prompt for dialogue generation.

        Returns:
            Generated dialogue string.
        """
        log.debug("generating_dialogue", model=self.dialogue_model)

        response = await self.client.messages.create(
            model=self.dialogue_model,
            max_tokens=300,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        log.debug("dialogue_generated", length=len(text))

        return text

    @async_retry(max_attempts=3)
    async def make_decision(
        self, system: str, prompt: str, choices: list[str]
    ) -> str:
        """Make a strategic decision using Sonnet model.

        Args:
            system: System prompt with personality and role.
            prompt: User prompt for decision.
            choices: List of valid choices.

        Returns:
            One of the choices (or random fallback if parsing fails).
        """
        log.debug(
            "making_decision",
            model=self.decision_model,
            num_choices=len(choices),
        )

        response = await self.client.messages.create(
            model=self.decision_model,
            max_tokens=150,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        log.debug("decision_response", response=text)

        # Parse response to extract a valid choice
        decision = self._parse_choice(text, choices)

        if decision:
            log.info("decision_made", choice=decision)
            return decision

        # Fallback to random if parsing fails
        fallback = random.choice(choices)
        log.warning(
            "decision_parse_failed",
            response=text,
            fallback=fallback,
        )
        return fallback

    @async_retry(max_attempts=3)
    async def analyze_odds(self, game_summary: str) -> dict[str, float]:
        """Analyze game state and return probability estimates.

        Args:
            game_summary: Summary of current game state.

        Returns:
            Dict with probability estimates for various outcomes.
        """
        log.debug("analyzing_odds", model=self.oddsmaker_model)

        prompt = f"""Analyze this Mafia game state and provide probability estimates:

{game_summary}

Provide probabilities (0.0 to 1.0) for:
1. Mafia winning
2. Citizens winning
3. Each alive agent being mafia

Format your response as:
mafia_win: 0.X
citizen_win: 0.X
agent_name: 0.X
"""

        response = await self.client.messages.create(
            model=self.oddsmaker_model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        log.debug("odds_response", response=text)

        # Parse probabilities
        odds = self._parse_odds(text)

        return odds

    def _parse_choice(self, text: str, choices: list[str]) -> str | None:
        """Parse response text to extract a valid choice.

        Args:
            text: Response text from Claude.
            choices: List of valid choices.

        Returns:
            Matched choice or None if no match found.
        """
        # Try exact match first (case-insensitive)
        text_lower = text.lower()
        for choice in choices:
            if choice.lower() == text_lower:
                return choice

        # Try substring match
        for choice in choices:
            if choice.lower() in text_lower:
                return choice

        # Try to find any choice name in the text
        for choice in choices:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(choice) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                return choice

        return None

    def _parse_odds(self, text: str) -> dict[str, float]:
        """Parse odds from response text.

        Args:
            text: Response text with probability estimates.

        Returns:
            Dict of outcome to probability. Returns uniform distribution on failure.
        """
        odds = {}

        # Extract probabilities using regex
        # Pattern: "name: 0.XX" or "name: XX%" (names can have digits/underscores)
        pattern = r"([a-zA-Z][a-zA-Z0-9_]*):\s*(-?\d*\.?\d+%?)"

        matches = re.findall(pattern, text)

        for name, value in matches:
            try:
                # Convert percentage to decimal if needed
                if "%" in value:
                    prob = float(value.rstrip("%")) / 100
                else:
                    prob = float(value)

                # Clamp to valid range
                odds[name] = max(0.0, min(1.0, prob))
            except ValueError:
                continue

        # Fallback: uniform distribution
        if not odds:
            log.warning("odds_parse_failed", text=text)
            odds = {"mafia_win": 0.5, "citizen_win": 0.5}

        return odds
