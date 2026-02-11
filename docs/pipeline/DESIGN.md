# MafiaAI - Design Document

## Overview
7 AI agents play Mafia. Spectators watch live via WebSocket + bet with play money.

## Architecture

```
mafia-ai/
├── src/
│   ├── __init__.py
│   ├── main.py                    # CLI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py            # Pydantic BaseSettings (.env)
│   │   └── constants.py           # Role, Phase, BetType enums, game constants
│   ├── models/
│   │   ├── __init__.py
│   │   ├── game.py                # GameState, GameConfig, RoundResult (frozen)
│   │   ├── agent.py               # Personality, AgentState (frozen)
│   │   ├── betting.py             # Bet, BettingPool, OddsBoard (frozen)
│   │   └── events.py              # WSEvent (frozen)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── game_engine.py         # State machine orchestrator (run_game loop)
│   │   ├── phase_handlers.py      # Night/Day/Vote phase logic
│   │   ├── role_assigner.py       # Random role assignment
│   │   └── win_checker.py         # Win condition evaluation
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent ABC
│   │   ├── personalities.py       # 7 personality definitions
│   │   ├── prompts.py             # Prompt templates per role
│   │   ├── memory.py              # Immutable memory manager (rolling 10)
│   │   └── claude_client.py       # Claude API wrapper
│   ├── betting/
│   │   ├── __init__.py
│   │   ├── pool.py                # Pari-mutuel pool (5% house edge)
│   │   ├── odds.py                # Dynamic odds calculator
│   │   └── oddsmaker.py           # AI oddsmaker (Haiku analyzes game → odds)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI + WebSocket + static files
│   │   ├── routes.py              # REST endpoints
│   │   └── ws_manager.py          # WebSocket broadcast manager
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py            # aiosqlite + auto-migrations
│   │   ├── migrations/
│   │   │   └── 001_initial.sql
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py            # Generic async repo
│   │       ├── game_repo.py       # Game persistence
│   │       └── bet_repo.py        # Bet persistence
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # structlog setup
│       ├── retry.py               # async retry decorator
│       └── errors.py              # Custom exception hierarchy
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_engine.py
│   ├── test_betting.py
│   ├── test_agents.py
│   └── test_api.py
├── pyproject.toml
├── .env.example
└── data/                          # Runtime (gitignored)
```

---

## Enum & Constants Spec (`src/config/constants.py`)

```python
from enum import Enum

class Role(str, Enum):
    MAFIA = "mafia"
    DETECTIVE = "detective"
    CITIZEN = "citizen"

class Phase(str, Enum):
    LOBBY = "lobby"
    NIGHT = "night"
    DAY_DISCUSSION = "day_discussion"
    DAY_VOTE = "day_vote"
    GAME_OVER = "game_over"

class BetType(str, Enum):
    SIDE_WIN = "side_win"           # mafia or citizens win
    NEXT_ELIMINATION = "next_elimination"  # who gets eliminated next
    IS_MAFIA = "is_mafia"           # specific agent is mafia

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
```

---

## Model Specs (all `frozen=True`)

### `src/models/game.py`

```python
from pydantic import BaseModel, Field
from src.config.constants import Phase, Role
import uuid
from datetime import datetime

class GameConfig(BaseModel, frozen=True):
    total_players: int = 7
    mafia_count: int = 2
    detective_count: int = 1
    betting_window_seconds: int = 30
    starting_chips: int = 1000

class RoundResult(BaseModel, frozen=True):
    round_number: int
    phase: Phase
    eliminated: str | None = None  # agent name
    eliminated_role: Role | None = None
    votes: dict[str, str] = Field(default_factory=dict)  # voter → target
    night_kill: str | None = None
    detective_target: str | None = None
    detective_result: bool | None = None  # True = is mafia

class GameState(BaseModel, frozen=True):
    game_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phase: Phase = Phase.LOBBY
    round_number: int = 0
    alive_agents: tuple[str, ...] = ()
    dead_agents: tuple[str, ...] = ()
    role_map: dict[str, Role] = Field(default_factory=dict)  # agent_name → role
    rounds: tuple[RoundResult, ...] = ()
    winner: str | None = None  # "mafia" or "citizens" or None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
```

### `src/models/agent.py`

```python
from pydantic import BaseModel, Field

class Personality(BaseModel, frozen=True):
    name: str
    trait: str          # short tag: "strategist", "empath", etc.
    description: str    # 2-3 sentences for system prompt
    speaking_style: str # e.g., "formal and calculated", "warm and empathetic"
    suspicion_bias: float = 0.5  # 0=trusting, 1=paranoid

class AgentState(BaseModel, frozen=True):
    name: str
    personality: Personality
    role: Role | None = None  # assigned at game start
    is_alive: bool = True
    memory: tuple[str, ...] = ()  # rolling last 10 events
    # Secret knowledge (mafia knows partners, detective knows investigations)
    known_roles: dict[str, Role] = Field(default_factory=dict)
```

### `src/models/betting.py`

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from src.config.constants import BetType

class Bet(BaseModel, frozen=True):
    bet_id: str
    game_id: str
    bettor_id: str  # spectator session id
    bet_type: BetType
    target: str  # "mafia", "citizens", or agent name
    amount: Decimal
    round_placed: int
    weight: Decimal = Decimal("1.0")  # early bet bonus weight

class BettingPool(BaseModel, frozen=True):
    game_id: str
    bet_type: BetType
    bets: tuple[Bet, ...] = ()
    total_amount: Decimal = Decimal("0")

class OddsBoard(BaseModel, frozen=True):
    game_id: str
    round_number: int
    mafia_win_prob: Decimal = Decimal("0.5")
    citizen_win_prob: Decimal = Decimal("0.5")
    elimination_odds: dict[str, Decimal] = Field(default_factory=dict)  # name → prob
    mafia_suspects: dict[str, Decimal] = Field(default_factory=dict)   # name → prob
```

### `src/models/events.py`

```python
from pydantic import BaseModel, Field
from typing import Any

class WSEvent(BaseModel, frozen=True):
    event_type: str  # phase_change, agent_message, vote_cast, elimination, odds_update, game_over, bet_placed
    data: dict[str, Any] = Field(default_factory=dict)
    game_id: str = ""
    timestamp: str = ""  # ISO format
```

---

## Settings Spec (`src/config/settings.py`)

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Claude API
    anthropic_api_key: SecretStr = SecretStr("")

    # Models
    dialogue_model: str = "claude-haiku-4-5-20251001"
    decision_model: str = "claude-sonnet-4-5-20250929"
    oddsmaker_model: str = "claude-haiku-4-5-20251001"

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Game
    betting_window_seconds: int = 30
    starting_chips: int = 1000

    # Database
    db_path: Path = Field(default=Path("data/mafia-ai.db"))

    # Logging
    log_level: str = "INFO"

def load_settings() -> Settings:
    return Settings()
```

---

## Error Hierarchy (`src/utils/errors.py`)

```python
class MafiaAIError(Exception):
    def __init__(self, message: str, *, hint: str | None = None) -> None:
        self.message = message
        self.hint = hint
        super().__init__(message)

class ConfigError(MafiaAIError): ...
class GameError(MafiaAIError): ...
class PhaseError(GameError): ...
class AgentError(MafiaAIError): ...
class APIError(AgentError): ...
class BettingError(MafiaAIError): ...
class StorageError(MafiaAIError): ...
```

---

## Engine Spec

### `src/engine/role_assigner.py`
- `assign_roles(agent_names: list[str], rng: random.Random | None = None) -> dict[str, Role]`
- Random assignment: 2 mafia, 1 detective, 4 citizens
- Returns frozen dict mapping name → role

### `src/engine/win_checker.py`
- `check_winner(alive_agents: tuple[str, ...], role_map: dict[str, Role]) -> str | None`
- Returns "citizens" if all mafia dead, "mafia" if mafia >= civilians, None if ongoing

### `src/engine/phase_handlers.py`
- `async handle_night(state: GameState, agents: dict[str, AgentState], claude: ClaudeClient) -> GameState`
  - Mafia agents choose kill target (Sonnet for decision)
  - Detective chooses investigation target (Sonnet)
  - Returns new state with night_kill applied
- `async handle_day_discussion(state: GameState, agents: dict[str, AgentState], claude: ClaudeClient, event_callback) -> list[WSEvent]`
  - Each alive agent makes up to 2 statements (Haiku for dialogue)
  - Returns list of agent_message events
- `async handle_day_vote(state: GameState, agents: dict[str, AgentState], claude: ClaudeClient) -> GameState`
  - Each alive agent votes to eliminate someone (Sonnet)
  - Majority vote eliminates, ties = no elimination
  - Returns new state

### `src/engine/game_engine.py`
- `GameEngine` class with `async run_game(event_callback)` method
- State machine: LOBBY → NIGHT → DAY_DISCUSSION → DAY_VOTE → (repeat or GAME_OVER)
- `event_callback: Callable[[WSEvent], Awaitable[None]]` for broadcasting events
- Uses immutable state transitions (always create new GameState)

---

## Agent Spec

### `src/agents/base.py`
```python
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, state: AgentState, claude_client: ClaudeClient):
        self.state = state
        self.claude = claude_client

    @abstractmethod
    async def generate_statement(self, game_state: GameState, context: str) -> str: ...

    @abstractmethod
    async def vote(self, game_state: GameState, candidates: list[str]) -> str: ...

    def update_state(self, **kwargs) -> 'BaseAgent':
        """Return new agent with updated state (immutable)."""
        new_state = self.state.model_copy(update=kwargs)
        return self.__class__(new_state, self.claude)
```

### `src/agents/personalities.py`
Define 7 personalities:
1. **Viktor** - strategist, formal/calculated, suspicion_bias=0.7
2. **Luna** - empath, warm/empathetic, suspicion_bias=0.3
3. **Rex** - bully, aggressive/confrontational, suspicion_bias=0.8
4. **Sage** - wise elder, measured/philosophical, suspicion_bias=0.5
5. **Nova** - wildcard, unpredictable/chaotic, suspicion_bias=0.5
6. **Iris** - observer, quiet/analytical, suspicion_bias=0.6
7. **Blaze** - hothead, impulsive/passionate, suspicion_bias=0.9

### `src/agents/prompts.py`
Template strings for:
- System prompt (personality + role + game rules)
- Night action prompt (mafia: choose kill, detective: choose investigate)
- Discussion prompt (generate statement given game context)
- Vote prompt (choose who to eliminate)
- Each includes game history context from memory

### `src/agents/memory.py`
```python
class AgentMemory:
    """Immutable rolling memory of last 10 game events."""

    def __init__(self, entries: tuple[str, ...] = ()):
        self._entries = entries

    def add(self, event: str) -> 'AgentMemory':
        """Return new memory with event added (max 10)."""
        new_entries = (*self._entries, event)[-10:]
        return AgentMemory(new_entries)

    def format_for_prompt(self) -> str:
        """Format memory entries as context string."""
```

### `src/agents/claude_client.py`
```python
class ClaudeClient:
    def __init__(self, settings: Settings):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key.get_secret_value())
        self.dialogue_model = settings.dialogue_model
        self.decision_model = settings.decision_model

    async def generate_dialogue(self, system: str, prompt: str) -> str:
        """Haiku for fast dialogue generation."""

    async def make_decision(self, system: str, prompt: str, choices: list[str]) -> str:
        """Sonnet for strategic decisions. Returns one of choices."""

    async def analyze_odds(self, game_summary: str) -> dict:
        """Haiku for odds analysis. Returns structured probabilities."""
```

**CRITICAL**: Decision responses must be parsed to extract a valid choice. If parsing fails, fallback to random.choice(choices).

---

## Database Schema (`src/storage/migrations/001_initial.sql`)

```sql
CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    phase TEXT NOT NULL DEFAULT 'lobby',
    round_number INTEGER NOT NULL DEFAULT 0,
    winner TEXT,
    role_map_json TEXT NOT NULL DEFAULT '{}',
    state_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at TEXT
);

CREATE TABLE IF NOT EXISTS game_rounds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    round_number INTEGER NOT NULL,
    phase TEXT NOT NULL,
    eliminated TEXT,
    eliminated_role TEXT,
    votes_json TEXT NOT NULL DEFAULT '{}',
    night_kill TEXT,
    detective_target TEXT,
    detective_result INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bets (
    bet_id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL REFERENCES games(game_id),
    bettor_id TEXT NOT NULL,
    bet_type TEXT NOT NULL,
    target TEXT NOT NULL,
    amount REAL NOT NULL,
    round_placed INTEGER NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    settled INTEGER NOT NULL DEFAULT 0,
    payout REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS spectators (
    session_id TEXT PRIMARY KEY,
    chips REAL NOT NULL DEFAULT 1000,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Betting Spec

### `src/betting/pool.py`
- Pari-mutuel: all bets go into pool, winners split proportionally
- `calculate_payout(pool: BettingPool, winner: str) -> dict[str, Decimal]`
  - Total pool * 0.95 (5% house edge) distributed to winning bets
  - Weighted by early bet multiplier

### `src/betting/odds.py`
- `calculate_implied_odds(pool: BettingPool) -> dict[str, Decimal]`
  - Based on bet distribution in pool
- `apply_early_bonus(bet: Bet, round_number: int) -> Bet`
  - Round 0: 1.5x weight, Round 1: 1.2x, else 1.0x

### `src/betting/oddsmaker.py`
- `async calculate_ai_odds(game_state: GameState, claude: ClaudeClient) -> OddsBoard`
  - Summarize game state → send to Haiku → parse probabilities
  - Fallback: uniform distribution if parsing fails

---

## File Ownership Map

| Agent | Directories/Files |
|-------|-------------------|
| p-impl-core | src/config/, src/models/, src/utils/, src/storage/, pyproject.toml, .env.example, all __init__.py, .gitignore |
| p-impl-engine | src/engine/, src/agents/, src/main.py |
| p-test-writer | tests/ |

---

## Reuse from arb-bot

Adapt these files (change imports/names, keep patterns):
- `arb-bot/src/utils/logger.py` → suppress "anthropic", "httpx" instead of "ccxt"
- `arb-bot/src/utils/retry.py` → retryable on `anthropic.APIError` instead of exchange errors
- `arb-bot/src/storage/database.py` → 100% drop-in (migration dir auto-detected)
- `arb-bot/src/storage/repositories/base.py` → 100% drop-in

## Handoff
- **Attempted**: Full design spec
- **Worked**: Complete architecture, all model specs, game flow defined
- **Failed**: N/A (design phase)
- **Remaining**: Implementation (P1)
