"""Role assignment logic for game initialization."""

import random

from src.config.constants import CITIZEN_COUNT, DETECTIVE_COUNT, MAFIA_COUNT, Role


def assign_roles(
    agent_names: list[str], rng: random.Random | None = None
) -> dict[str, Role]:
    """Randomly assign roles to agents.

    Args:
        agent_names: List of agent names to assign roles to.
        rng: Optional Random instance for deterministic tests.

    Returns:
        Frozen dict mapping agent name to role.

    Raises:
        ValueError: If agent_names length doesn't match expected player count.
    """
    if len(agent_names) != MAFIA_COUNT + DETECTIVE_COUNT + CITIZEN_COUNT:
        raise ValueError(
            f"Expected {MAFIA_COUNT + DETECTIVE_COUNT + CITIZEN_COUNT} agents, "
            f"got {len(agent_names)}"
        )

    # Use provided RNG or create a new one
    rng = rng or random.Random()

    # Create role pool
    roles = (
        [Role.MAFIA] * MAFIA_COUNT
        + [Role.DETECTIVE] * DETECTIVE_COUNT
        + [Role.CITIZEN] * CITIZEN_COUNT
    )

    # Shuffle and assign
    shuffled_names = agent_names.copy()
    rng.shuffle(shuffled_names)

    return dict(zip(shuffled_names, roles))
