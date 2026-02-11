# MafiaAI

## Overview

AI Mafia game where 7 agents with distinct personalities compete. Spectators watch real-time action via WebSocket and place bets on outcomes. Hackathon project using Claude API (Haiku for dialogue, Sonnet for decisions).

## Running

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

Or use directly:
```bash
.venv/bin/python -m src.main
```

### Run Tests
```bash
.venv/bin/python -m pytest tests/ -v --tb=short
```

### Run with Coverage
```bash
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

## Configuration

Create `.env` in project root:
```
ANTHROPIC_API_KEY=sk-xxx-your-key-here
```

Other environment variables (optional):
- `DIALOGUE_MODEL=claude-haiku-4-5-20251001`
- `DECISION_MODEL=claude-sonnet-4-5-20250929`
- `ODDSMAKER_MODEL=claude-haiku-4-5-20251001`
- `PORT=8080`
- `HOST=0.0.0.0`
- `BETTING_WINDOW_SECONDS=30`
- `STARTING_CHIPS=1000`
- `DB_PATH=data/mafia-ai.db`
- `LOG_LEVEL=INFO`

## Architecture

### Design Principles

1. **Immutability** — All Pydantic models are `frozen=True`. Never mutate state; create new instances.
2. **State Machine** — Game flows: LOBBY → NIGHT → DAY_DISCUSSION → DAY_VOTE → (repeat or GAME_OVER)
3. **Async Throughout** — AsyncIO-based, aiosqlite, async Anthropic client, FastAPI with WebSocket
4. **Functional Transitions** — GameState transitions return new GameState; no in-place mutations
5. **Memory Management** — AgentMemory holds last 10 game events (immutable rolling window)

### Core Modules

| Module | Purpose |
|--------|---------|
| `src/config/` | Settings, enums (Role, Phase, BetType), game constants |
| `src/models/` | Pydantic frozen models (GameState, AgentState, Bet, OddsBoard, WSEvent) |
| `src/engine/` | Game state machine, phase handlers (Night/Day/Vote) |
| `src/agents/` | AI personalities, prompts, Claude API client, memory |
| `src/betting/` | Pari-mutuel pool, odds calculation, AI oddsmaker |
| `src/api/` | FastAPI server, WebSocket manager, REST routes |
| `src/storage/` | aiosqlite, migrations, repositories |
| `src/utils/` | Logging (structlog), retry logic, error hierarchy |

### Game Flow

```
1. LOBBY: Initialize 7 agents, assign random roles
2. NIGHT: Mafia kills, Detective investigates (Claude Sonnet)
3. DAY_DISCUSSION: Each agent makes 2 statements (Claude Haiku)
4. DAY_VOTE: Each agent votes (Claude Sonnet)
5. Check winner:
   - Citizens win if all mafia dead
   - Mafia wins if mafia >= citizens
   - Otherwise repeat from NIGHT
6. GAME_OVER: Announce winner, settle bets
```

### Key Classes

#### GameState (frozen)
```python
game_id: str
phase: Phase
round_number: int
alive_agents: tuple[str, ...]
dead_agents: tuple[str, ...]
role_map: dict[str, Role]  # agent_name → role
rounds: tuple[RoundResult, ...]
winner: str | None  # "citizens" or "mafia"
```

#### AgentState (frozen)
```python
name: str
personality: Personality
role: Role | None
is_alive: bool
memory: tuple[str, ...]  # last 10 events
known_roles: dict[str, Role]  # secret knowledge
```

#### Personality (frozen)
```python
name: str
trait: str  # "strategist", "empath", etc.
description: str  # system prompt context
speaking_style: str
suspicion_bias: float  # 0=trusting, 1=paranoid
```

#### BettingPool (frozen)
```python
game_id: str
bet_type: BetType  # SIDE_WIN, NEXT_ELIMINATION, IS_MAFIA
bets: tuple[Bet, ...]
total_amount: Decimal
```

## Key Patterns

### 1. Immutable State Transitions

```python
# WRONG: Mutation
state.phase = Phase.NIGHT

# CORRECT: Create new state
new_state = state.model_copy(update={"phase": Phase.NIGHT})
```

### 2. Agent Personality-Driven Decisions

- System prompt includes personality description + speaking style
- Haiku generates dialogue (fast, contextual)
- Sonnet makes vote/kill decisions (strategic, accurate)
- Fallback to random.choice() if Claude response can't be parsed

### 3. Immutable Memory

```python
# Memory is a rolling tuple of last 10 events
memory = AgentMemory(entries=())
memory = memory.add("Event 1")
memory = memory.add("Event 2")  # Returns new memory
```

### 4. WebSocket Broadcasting

```python
# All game events broadcast to connected clients
await ws_manager.broadcast(WSEvent(
    event_type="agent_message",
    data={"agent": "Viktor", "message": "..."},
    game_id=game_state.game_id,
    timestamp=datetime.now().isoformat()
))
```

### 5. Pari-Mutuel Betting

- All bets pool together
- House takes 5% cut
- Winners split 95% weighted by early bet bonuses
- Round 0: 1.5x weight, Round 1: 1.2x, else 1.0x

### 6. Claude API Retry Logic

```python
# Retry on APIError, exponential backoff
@async_retry(max_attempts=3, backoff=exponential)
async def generate_dialogue(...): ...

# Fallback to random choice if parsing fails
try:
    decision = parse_decision(response)
except ValueError:
    decision = random.choice(valid_choices)
```

## File Structure

```
src/
├── __init__.py
├── main.py                      # CLI entry point
├── config/
│   ├── __init__.py
│   ├── settings.py              # Pydantic BaseSettings (.env)
│   └── constants.py             # Enums, game constants
├── models/
│   ├── __init__.py
│   ├── game.py                  # GameState, GameConfig, RoundResult
│   ├── agent.py                 # Personality, AgentState
│   ├── betting.py               # Bet, BettingPool, OddsBoard
│   └── events.py                # WSEvent
├── engine/
│   ├── __init__.py
│   ├── game_engine.py           # State machine orchestrator
│   ├── phase_handlers.py        # Night/Day/Vote logic
│   ├── role_assigner.py         # Random role assignment
│   └── win_checker.py           # Win condition evaluation
├── agents/
│   ├── __init__.py
│   ├── base.py                  # BaseAgent ABC
│   ├── personalities.py         # 7 personality definitions
│   ├── prompts.py               # Prompt templates
│   ├── memory.py                # Immutable memory manager
│   └── claude_client.py         # Claude API wrapper
├── betting/
│   ├── __init__.py
│   ├── pool.py                  # Pari-mutuel logic
│   ├── odds.py                  # Odds calculation
│   └── oddsmaker.py             # AI odds analysis
├── api/
│   ├── __init__.py
│   ├── server.py                # FastAPI + WebSocket + static files
│   ├── routes.py                # REST endpoints
│   └── ws_manager.py            # WebSocket broadcast
├── storage/
│   ├── __init__.py
│   ├── database.py              # aiosqlite + migrations
│   ├── migrations/
│   │   └── 001_initial.sql
│   └── repositories/
│       ├── __init__.py
│       ├── base.py              # Generic async repo
│       ├── game_repo.py         # Game persistence
│       └── bet_repo.py          # Bet persistence
└── utils/
    ├── __init__.py
    ├── logger.py                # structlog setup
    ├── retry.py                 # async retry decorator
    └── errors.py                # Custom exception hierarchy

tests/
├── __init__.py
├── conftest.py                  # pytest fixtures
├── test_engine.py               # Game engine tests
├── test_agents.py               # Agent tests
├── test_betting.py              # Betting tests
└── test_api.py                  # API tests

static/
├── index.html                   # Dashboard
├── style.css                    # Styling
└── app.js                       # WebSocket client

pyproject.toml                    # Dependencies, pytest config
.env.example                      # Environment template
```

## Testing

### Test Structure
- **Unit Tests** — Individual functions (engine, agents, betting)
- **Integration Tests** — Full game flow with mocked Claude
- **Async Support** — pytest-asyncio for all async code

### Running Tests
```bash
# All tests
pytest tests/ -v

# Single file
pytest tests/test_engine.py -v

# Single test
pytest tests/test_engine.py::test_game_starts_in_lobby -v

# With output (don't capture stdout/stderr)
pytest tests/ -s

# Coverage report
pytest tests/ --cov=src --cov-report=html
```

### Coverage Target
- Aim for 80%+ coverage
- Engine, agents, betting should be 100%
- API/server skips are acceptable (integration heavy)

## Common Tasks

### Add a New Game Phase
1. Add Phase enum variant in `src/config/constants.py`
2. Create handler in `src/engine/phase_handlers.py`
3. Add transition logic in `src/engine/game_engine.py`
4. Write tests in `tests/test_engine.py`

### Modify a Personality
1. Edit `src/agents/personalities.py`
2. Update system prompt in `src/agents/prompts.py` if needed
3. Run `pytest tests/test_agents.py -v` to verify

### Add a New Bet Type
1. Add `BetType` enum in `src/config/constants.py`
2. Update `BettingPool` model in `src/models/betting.py`
3. Add payout logic in `src/betting/pool.py`
4. Write tests in `tests/test_betting.py`

### Debug Claude API Calls
1. Check `src/utils/logger.py` for log setup
2. Run with `LOG_LEVEL=DEBUG`
3. Check `src/agents/claude_client.py` for API error handling

## Environment

**Python:** 3.11+
**Async:** asyncio throughout
**API:** Anthropic Claude (Haiku + Sonnet)
**Web:** FastAPI + WebSocket
**DB:** aiosqlite (SQLite)
**Logging:** structlog

## Git Workflow

- Feature branches: `feature/description`
- Commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- All tests passing before merge
- PRs require code review

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ANTHROPIC_API_KEY not configured` | Set in `.env` or export `ANTHROPIC_API_KEY` |
| Tests timeout | Increase pytest timeout: `pytest --timeout=30` |
| Database locked | Remove `data/mafia-ai.db` and restart |
| WebSocket not connecting | Check port 8080 is available, check firewall |
| Claude API errors | Check rate limits, API key validity, network |
| Memory grows unbounded | AgentMemory rolling window keeps max 10 events |

## References

- Anthropic API: https://docs.anthropic.com
- Pydantic v2: https://docs.pydantic.dev
- FastAPI: https://fastapi.tiangolo.com
- aiosqlite: https://github.com/omnilib/aiosqlite
- structlog: https://www.structlog.org
