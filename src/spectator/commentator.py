"""AI spectator commentator — 3 personas react to game events."""

import asyncio
import random
import time

from src.agents.llm_client import LLMClient
from src.utils.logger import get_logger

log = get_logger(__name__)

PERSONAS = (
    {
        "name": "degen_0x",
        "style": "Degenerate gambler. Use crypto/betting slang: 'bruh', 'odds', 'all in', 'rug', 'ngmi'. Short, hype.",
    },
    {
        "name": "theorist_",
        "style": "Conspiracy theorist. Overanalyze tiny details. 'Did anyone notice...', 'classic tell', 'suspicious'.",
    },
    {
        "name": "casually__",
        "style": "Gen-Z casual viewer. Use 'lol', 'ngl', 'lowkey', 'literally'. Chill, sometimes sarcastic.",
    },
)

TRIGGER_EVENTS = frozenset({
    "phase_change",
    "elimination",
    "game_over",
    "odds_update",
})


class SpectatorCommentator:
    """Generates AI spectator chat messages in response to game events."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client
        self._last_comment_time: float = 0.0
        self._cooldown: float = 5.0

    async def on_game_event(
        self,
        event_type: str,
        data: dict,
        broadcast_chat: "asyncio.coroutines" = None,
    ) -> None:
        """React to a game event. Fire-and-forget safe.

        Args:
            event_type: The WSEvent event_type string.
            data: The event data dict.
            broadcast_chat: Async callable(name, text, is_ai) to broadcast a spec chat message.
        """
        if event_type not in TRIGGER_EVENTS:
            return
        if broadcast_chat is None:
            return

        now = time.monotonic()
        if now - self._last_comment_time < self._cooldown:
            return

        persona = random.choice(PERSONAS)
        delay = random.uniform(2.0, 8.0)

        try:
            await asyncio.sleep(delay)

            # Build a concise event summary for the LLM
            summary = self._summarize_event(event_type, data)
            if not summary:
                return

            system = (
                f"You are '{persona['name']}', a spectator in a Mafia game live chat. "
                f"Style: {persona['style']} "
                "Write ONE short comment (max 15 words). No hashtags. No emojis. Just raw chat text."
            )
            prompt = f"React to this game event: {summary}"

            text = await self._llm.generate_dialogue(system, prompt)
            text = text.strip().strip('"').strip("'")

            # Truncate if needed
            if len(text) > 120:
                text = text[:117] + "..."

            self._last_comment_time = time.monotonic()
            await broadcast_chat(persona["name"], text, True)
            log.debug("ai_comment_sent", persona=persona["name"], text=text)

        except Exception as exc:
            log.debug("ai_comment_failed", error=str(exc))

    @staticmethod
    def _summarize_event(event_type: str, data: dict) -> str:
        """Build a short summary string for the LLM prompt."""
        if event_type == "phase_change":
            phase = data.get("phase", "unknown")
            round_num = data.get("round", "?")
            return f"Phase changed to {phase}, round {round_num}"
        if event_type == "elimination":
            agent = data.get("agent", "someone")
            reason = data.get("reason", "eliminated")
            role = data.get("role", "")
            role_str = f" ({role})" if role else ""
            return f"{agent}{role_str} was {reason}"
        if event_type == "game_over":
            winner = data.get("winner", "unknown")
            return f"Game over! {winner} won"
        if event_type == "odds_update":
            mafia = data.get("mafia_win_prob", 0.5)
            return f"Odds shifted — mafia win probability: {mafia:.0%}"
        return ""
