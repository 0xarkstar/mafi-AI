"""Game constants and enums."""

from enum import Enum


class Role(str, Enum):
    """Player role in the game."""

    MAFIA = "mafia"
    DETECTIVE = "detective"
    CITIZEN = "citizen"


class Phase(str, Enum):
    """Game phase."""

    LOBBY = "lobby"
    NIGHT = "night"
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    REVEAL = "reveal"
    GAME_OVER = "game_over"


class PlayerType(str, Enum):
    """Type of player in the game."""

    HOUSE_AI = "house_ai"  # Server's AI agent
    MOLTBOOK_AGENT = "moltbook_agent"  # External autonomous AI via API
    AGENT_HUMAN = "agent_human"  # Human using agent account (WebSocket)
    HUMAN = "human"  # Regular human player (WebSocket)


class BetType(str, Enum):
    """Type of bet spectators can place."""

    SIDE_WIN = "side_win"  # mafia or citizens win
    NEXT_ELIMINATION = "next_elimination"  # who gets eliminated next
    IS_MAFIA = "is_mafia"  # specific agent is mafia
    IS_AI_OR_HUMAN = "is_ai_or_human"  # bet on whether player is AI or human


# Game constants
TOTAL_PLAYERS = 7
MAFIA_COUNT = 2
DETECTIVE_COUNT = 1
CITIZEN_COUNT = 4
MAX_DISCUSSION_STATEMENTS = 2  # per agent per day
BETTING_WINDOW_SECONDS = 30
HOUSE_EDGE = 0.05  # 5%
EARLY_BET_MULTIPLIERS = {0: 1.5, 1: 1.2}  # round → weight multiplier
DEFAULT_STARTING_CHIPS = 1000
