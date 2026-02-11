"""Agent state models."""

from pydantic import BaseModel, Field

from src.config.constants import Role


class Personality(BaseModel, frozen=True):
    """Agent personality definition."""

    name: str
    trait: str  # short tag: "strategist", "empath", etc.
    description: str  # 2-3 sentences for system prompt
    speaking_style: str  # e.g., "formal and calculated", "warm and empathetic"
    suspicion_bias: float = 0.5  # 0=trusting, 1=paranoid


class AgentState(BaseModel, frozen=True):
    """Immutable agent state."""

    name: str
    personality: Personality
    role: Role | None = None  # assigned at game start
    is_alive: bool = True
    memory: tuple[str, ...] = ()  # rolling last 10 events
    # Secret knowledge (mafia knows partners, detective knows investigations)
    known_roles: dict[str, Role] = Field(default_factory=dict)
