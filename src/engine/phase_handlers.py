"""Phase handling logic — re-exports for backward compatibility."""

from src.engine.phase_day import handle_day_discussion
from src.engine.phase_night import handle_night
from src.engine.phase_vote import handle_day_vote

__all__ = ["handle_night", "handle_day_discussion", "handle_day_vote"]
