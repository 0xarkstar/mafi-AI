"""LLM-based game analysis for betting decisions."""

import re
from decimal import Decimal

from openai import AsyncOpenAI

from src.ai_bettor.models import BetDecision, GameObservation
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GameAnalyzer:
    """LLM-based game analyzer for betting decisions."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize analyzer with OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model to use for analysis
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def analyze_and_decide(
        self, observation: GameObservation, balance: Decimal
    ) -> BetDecision:
        """Analyze game state and produce betting decision.

        Args:
            observation: Current game state
            balance: Available balance

        Returns:
            BetDecision with should_bet=False on any error
        """
        try:
            prompt = self._build_prompt(observation, balance)
            response = await self._call_llm(prompt)
            decision = self._parse_response(response)
            logger.info(
                "bet_decision_generated",
                should_bet=decision.should_bet,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
            )
            return decision
        except Exception as e:
            logger.warning("bet_analysis_failed", error=str(e))
            return BetDecision(
                should_bet=False,
                bet_type="side_win",
                target="citizens",
                amount_usdc=Decimal("0"),
                confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
            )

    def _build_prompt(self, observation: GameObservation, balance: Decimal) -> str:
        """Build LLM prompt from observation."""
        recent_events_str = "\n".join(observation.recent_events) or "No events yet"
        odds_str = "\n".join(
            f"{k}: {v}" for k, v in observation.current_odds.items()
        ) or "No odds available"

        return f"""# Mafia Game Betting Analysis

## Game State
Phase: {observation.phase} | Round: {observation.round_number}
Alive: {', '.join(observation.alive_agents)}
Dead: {', '.join(observation.dead_agents)}

## Recent Events
{recent_events_str}

## Current Odds
{odds_str}

## Your Balance: {balance} USDC

## Decide
Respond in exactly this format:
bet: yes/no
bet_type: side_win | is_mafia | next_elimination | is_ai_or_human
target: <target>
amount: <1.00-10.00>
confidence: <0.0-1.0>
reasoning: <brief one line>"""

    async def _call_llm(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert Mafia game analyst who makes strategic betting decisions.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, response: str) -> BetDecision:
        """Parse LLM response into BetDecision.

        Args:
            response: Raw LLM response text

        Returns:
            Parsed BetDecision

        Raises:
            ValueError: If response cannot be parsed
        """
        lines = response.strip().split("\n")
        parsed = {}

        for line in lines:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip().lower()] = value.strip()

        # Extract fields
        bet_str = parsed.get("bet", "no").lower()
        should_bet = bet_str in ("yes", "true", "1")

        bet_type = parsed.get("bet_type", "side_win")
        target = parsed.get("target", "citizens")

        # Parse amount
        amount_str = parsed.get("amount", "0")
        amount_match = re.search(r"[\d.]+", amount_str)
        amount = Decimal(amount_match.group()) if amount_match else Decimal("0")

        # Parse confidence
        confidence_str = parsed.get("confidence", "0.0")
        confidence_match = re.search(r"[\d.]+", confidence_str)
        confidence = float(confidence_match.group()) if confidence_match else 0.0

        reasoning = parsed.get("reasoning", "No reasoning provided")

        return BetDecision(
            should_bet=should_bet,
            bet_type=bet_type,
            target=target,
            amount_usdc=amount,
            confidence=confidence,
            reasoning=reasoning,
        )
