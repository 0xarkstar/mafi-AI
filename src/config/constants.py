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
    GAME_OVER = "game_over"


class BetType(str, Enum):
    """Type of bet spectators can place."""

    SIDE_WIN = "side_win"  # mafia or citizens win
    NEXT_ELIMINATION = "next_elimination"  # who gets eliminated next
    IS_MAFIA = "is_mafia"  # specific agent is mafia


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
