"""Win condition checking logic."""

from src.config.constants import Role


def check_winner(
    alive_agents: tuple[str, ...], role_map: dict[str, Role]
) -> str | None:
    """Check if a side has won the game.

    Args:
        alive_agents: Tuple of agent names still alive.
        role_map: Mapping of agent name to role.

    Returns:
        "citizens" if all mafia are dead.
        "mafia" if mafia count >= non-mafia count.
        None if game is ongoing.
    """
    # Count alive mafia and non-mafia
    alive_mafia = sum(1 for name in alive_agents if role_map[name] == Role.MAFIA)
    alive_non_mafia = len(alive_agents) - alive_mafia

    # Citizens win if all mafia are dead
    if alive_mafia == 0:
        return "citizens"

    # Mafia win if they equal or outnumber non-mafia
    if alive_mafia >= alive_non_mafia:
        return "mafia"

    # Game ongoing
    return None
