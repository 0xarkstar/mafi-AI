"""Prompt template functions for Claude AI interactions."""

from src.config.constants import Role
from src.models.agent import Personality
from src.models.game import RoundResult


def build_system_prompt(
    personality: Personality, role: Role, game_rules: str
) -> str:
    """Build system prompt for agent with personality and role.

    Args:
        personality: Agent's personality definition.
        role: Agent's assigned role (mafia, detective, or citizen).
        game_rules: Game rules description.

    Returns:
        System prompt string.
    """
    role_instructions = {
        Role.MAFIA: (
            "You are MAFIA. Your goal is to eliminate citizens while avoiding detection. "
            "At night, you and your mafia partners choose who to kill. During the day, "
            "you must blend in and deflect suspicion onto others."
        ),
        Role.DETECTIVE: (
            "You are the DETECTIVE. Your goal is to identify and eliminate the mafia. "
            "At night, you can investigate one player to learn if they are mafia. "
            "Use this information carefully during day discussions."
        ),
        Role.CITIZEN: (
            "You are a CITIZEN. Your goal is to identify and vote out the mafia. "
            "You have no special powers, but you can use logic and observation "
            "to deduce who the mafia might be."
        ),
    }

    return f"""You are {personality.name}, a player in a game of Mafia.

PERSONALITY:
{personality.description}

Your speaking style is: {personality.speaking_style}

ROLE:
{role_instructions[role]}

GAME RULES:
{game_rules}

IMPORTANT:
- Stay in character as {personality.name}
- Use your {personality.speaking_style} speaking style
- Never reveal your role directly unless strategically necessary
- Make decisions that align with your personality and role
"""


def build_night_action_prompt(
    role: Role,
    alive_agents: tuple[str, ...],
    known_roles: dict[str, Role],
    memory: tuple[str, ...],
) -> str:
    """Build prompt for night action decisions.

    Args:
        role: Agent's role.
        alive_agents: Tuple of alive agent names.
        known_roles: Dict of known roles for this agent.
        memory: Tuple of recent memory entries.

    Returns:
        Night action prompt string.
    """
    memory_str = "\n".join(memory) if memory else "This is the first night."

    if role == Role.MAFIA:
        targets = [
            name for name in alive_agents if known_roles.get(name) != Role.MAFIA
        ]
        return f"""NIGHT PHASE - Choose who to eliminate.

RECENT EVENTS:
{memory_str}

ALIVE PLAYERS:
{', '.join(alive_agents)}

YOUR MAFIA PARTNERS:
{', '.join([name for name, r in known_roles.items() if r == Role.MAFIA and name in alive_agents])}

Choose one player to eliminate tonight from: {', '.join(targets)}

Consider:
- Who is most likely to be the detective?
- Who poses the greatest threat to your mafia team?
- Who would create the most confusion if eliminated?

Respond with ONLY the player's name.
"""

    elif role == Role.DETECTIVE:
        investigated = [name for name in known_roles if name in alive_agents]
        targets = [name for name in alive_agents if name not in investigated]

        return f"""NIGHT PHASE - Choose who to investigate.

RECENT EVENTS:
{memory_str}

ALIVE PLAYERS:
{', '.join(alive_agents)}

ALREADY INVESTIGATED:
{', '.join(investigated) if investigated else "None"}

YOUR INVESTIGATION RESULTS:
{', '.join([f"{name}: {'MAFIA' if r == Role.MAFIA else 'INNOCENT'}" for name, r in known_roles.items()])}

Choose one player to investigate from: {', '.join(targets)}

Consider:
- Who has been acting suspiciously?
- Who has been too quiet or too aggressive?
- What would help you most in tomorrow's vote?

Respond with ONLY the player's name.
"""

    return ""


def build_discussion_prompt(
    personality: Personality,
    role: Role,
    round_events: tuple[RoundResult, ...],
    memory: tuple[str, ...],
    alive_agents: tuple[str, ...],
) -> str:
    """Build prompt for day discussion statements.

    Args:
        personality: Agent's personality.
        role: Agent's role.
        round_events: Recent round results.
        memory: Tuple of memory entries.
        alive_agents: Tuple of alive agent names.

    Returns:
        Discussion prompt string.
    """
    memory_str = "\n".join(memory) if memory else "No previous events."

    # Summarize recent eliminations
    events_summary = []
    for result in round_events:
        if result.night_kill:
            events_summary.append(f"Night {result.round_number}: {result.night_kill} was killed")
        if result.eliminated:
            events_summary.append(
                f"Day {result.round_number}: {result.eliminated} was voted out (role: {result.eliminated_role})"
            )

    events_str = "\n".join(events_summary) if events_summary else "No eliminations yet."

    return f"""DAY DISCUSSION - Make a statement to the group.

RECENT ELIMINATIONS:
{events_str}

ALIVE PLAYERS:
{', '.join(alive_agents)}

YOUR MEMORY:
{memory_str}

As {personality.name} ({personality.speaking_style}), make a statement to the group.

Consider:
- What do recent eliminations tell you?
- Who seems suspicious based on their behavior?
- Who do you trust or distrust?
- What information can you share (without revealing your role directly)?

Make a natural statement that fits your personality. Keep it under 100 words.
"""


def build_vote_prompt(
    personality: Personality,
    role: Role,
    discussion_log: tuple[RoundResult, ...],
    alive_agents: tuple[str, ...],
    memory: tuple[str, ...],
) -> str:
    """Build prompt for voting decisions.

    Args:
        personality: Agent's personality.
        role: Agent's role.
        discussion_log: Recent discussion rounds.
        alive_agents: Tuple of alive agent names.
        memory: Tuple of memory entries.

    Returns:
        Vote prompt string.
    """
    memory_str = "\n".join(memory) if memory else "No previous events."

    # Don't include self in candidates
    candidates = [name for name in alive_agents if name != personality.name]

    return f"""VOTING PHASE - Choose who to eliminate.

YOUR MEMORY:
{memory_str}

ALIVE PLAYERS (excluding you):
{', '.join(candidates)}

As {personality.name}, decide who to vote for elimination.

Consider:
- Who has been most suspicious?
- What does your role tell you? (Mafia: protect your team; Detective: use your investigations; Citizen: use logic)
- Your personality bias (suspicion level: {personality.suspicion_bias})

Choose ONE player to vote for from: {', '.join(candidates)}

Respond with ONLY the player's name.
"""
