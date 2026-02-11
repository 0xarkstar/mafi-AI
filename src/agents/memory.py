"""Immutable agent memory manager."""


class AgentMemory:
    """Immutable rolling memory of last 10 game events."""

    def __init__(self, entries: tuple[str, ...] = ()):
        """Initialize memory with entries.

        Args:
            entries: Tuple of memory entries.
        """
        self._entries = entries

    def add(self, event: str) -> "AgentMemory":
        """Return new memory with event added (keeps last 10).

        Args:
            event: Event description to add.

        Returns:
            New AgentMemory instance with event added.
        """
        new_entries = (*self._entries, event)[-10:]
        return AgentMemory(new_entries)

    def format_for_prompt(self) -> str:
        """Format memory entries as context string.

        Returns:
            Formatted memory string for prompts.
        """
        if not self._entries:
            return "No previous events."

        lines = ["Recent events:"]
        for i, entry in enumerate(self._entries, 1):
            lines.append(f"{i}. {entry}")

        return "\n".join(lines)

    def __len__(self) -> int:
        """Return number of memory entries."""
        return len(self._entries)

    def __iter__(self):
        """Iterate over memory entries."""
        return iter(self._entries)
