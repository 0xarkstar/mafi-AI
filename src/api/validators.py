"""Player name validation helpers."""

import re

NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\- ]+$")


def validate_player_name(name: str) -> str | None:
    """Validate player name. Returns error message if invalid, None if valid."""
    if not name or not isinstance(name, str):
        return "Name must be a non-empty string"
    if len(name) < 1 or len(name) > 32:
        return "Name must be 1-32 characters"
    if not NAME_PATTERN.match(name):
        return "Name can only contain letters, numbers, spaces, hyphens, and underscores"
    return None
