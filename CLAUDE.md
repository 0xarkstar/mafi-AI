# MafiaAI

## Overview

AI Mafia game where 7 players (mix of House AI agents, external agents via Moltbook, and humans) compete. Spectators watch real-time action via WebSocket and place bets on outcomes. Hackathon project using OpenAI GPT-4o-mini for all AI operations, with optional on-chain betting on Monad testnet.

**Mixed-Player Arena** — Dynamic multi-player modes: all House AI, humans join via lobby, external AI agents via Moltbook API integration, identity betting on player types (AI vs Human).

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
OPENAI_API_KEY=your-openai-api-key
```

Core environment variables (optional):
- `DIALOGUE_MODEL=gpt-4o-mini`
- `DECISION_MODEL=gpt-4o-mini`
- `ODDSMAKER_MODEL=gpt-4o-mini`
- `PORT=8080`
- `HOST=0.0.0.0`
- `BETTING_WINDOW_SECONDS=30`
- `STARTING_CHIPS=1000`
- `DB_PATH=data/mafia-ai.db`
- `LOG_LEVEL=INFO`

Mixed-Player Arena variables (optional):
- `MOLTBOOK_API_URL=https://api.moltbook.io`
- `LOBBY_TIMEOUT_SECONDS=300` (5 minutes before auto-filling with House AI)
- `HUMAN_TURN_TIMEOUT=60` (1 minute for humans to make decisions)

Blockchain variables (optional - for on-chain betting):
- `BLOCKCHAIN_ENABLED=false`
- `BLOCKCHAIN_RPC_URL=https://testnet-rpc.monad.xyz`
- `BLOCKCHAIN_CHAIN_ID=10143`
- `BLOCKCHAIN_PRIVATE_KEY=0xyour-private-key`
- `BLOCKCHAIN_CONTRACT_ADDRESS=0xyour-deployed-contract-address`

## Architecture

### Design Principles

1. **Immutability** — All Pydantic models are `frozen=True`. Never mutate state; create new instances.
2. **State Machine** — Game flows: LOBBY → NIGHT → DAY_DISCUSSION → DAY_VOTE → (repeat or GAME_OVER)
3. **Async Throughout** — AsyncIO-based, aiosqlite, async LLM client (OpenAI SDK), FastAPI with WebSocket
4. **Functional Transitions** — GameState transitions return new GameState; no in-place mutations
5. **Memory Management** — AgentMemory holds last 10 game events (immutable rolling window)
6. **Blockchain Optional** — Falls back to chip betting if blockchain_enabled=False (default)

### Core Modules

| Module | Purpose |
|--------|---------|
| `src/config/` | Settings, enums (Role, Phase, PlayerType, BetType), game constants |
| `src/models/` | Pydantic frozen models (GameState, AgentState, Bet, OddsBoard, WSEvent) |
| `src/engine/` | Game state machine, phase handlers (Night/Day/Vote/Reveal) |
| `src/agents/` | AI personalities, prompts, OpenAI client, memory |
| `src/players/` | PlayerProtocol, HouseAIPlayer, MoltbookAgent, AgentHuman, Human |
| `src/lobby/` | LobbyManager for game setup and player registration |
| `src/moltbook/` | Moltbook API client for external agent integration |
| `src/betting/` | Pari-mutuel pool, odds calculation, AI oddsmaker, identity betting |
| `src/blockchain/` | Web3 provider, contract oracle (create, settle, lock games on-chain) |
| `src/api/` | FastAPI server, WebSocket manager, REST routes, blockchain config endpoint |
| `src/storage/` | aiosqlite, migrations, repositories |
| `src/utils/` | Logging (structlog), retry logic, error hierarchy |

### Game Flow

```
1. LOBBY: Players join (humans via WebSocket, external agents via Moltbook, house AI auto-fills)
   - Wait for 7 players or timeout, then auto-fill with House AI
2. (Optional) Create game on-chain if blockchain_enabled=True
3. NIGHT: Mafia kills, Detective investigates (OpenAI or human/agent input)
4. DAY_DISCUSSION: Each player makes 2 statements (OpenAI/Moltbook/human input)
5. DAY_VOTE: Each player votes (OpenAI/Moltbook/human input)
6. REVEAL: Optional phase to reveal player types (AI vs Human) for identity bets
7. Check winner:
   - Citizens win if all mafia dead
   - Mafia wins if mafia >= citizens
   - Otherwise repeat from NIGHT
8. GAME_OVER: Announce winner, settle bets
9. (Optional) Settle result on-chain if blockchain_enabled=True
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
player_type_map: dict[str, PlayerType]  # agent_name → player type (HOUSE_AI, MOLTBOOK_AGENT, AGENT_HUMAN, HUMAN)
rounds: tuple[RoundResult, ...]
winner: str | None  # "citizens" or "mafia"
```

#### PlayerProtocol (runtime_checkable)
```python
name: str
player_type: PlayerType

async def generate_statement(context: TurnContext) -> str: ...
async def vote(context: TurnContext, candidates: list[str]) -> str: ...
async def night_action(context: TurnContext, targets: list[str]) -> str: ...
```

#### TurnContext (frozen)
```python
alive_agents: tuple[str, ...]
role: Role
known_roles: dict[str, Role]
memory: tuple[str, ...]
round_number: int
round_history: tuple[RoundResult, ...]
personality: Personality | None  # For House AI
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

## Mixed-Player Arena Architecture

### Overview

The Mixed-Player Arena enables dynamic multiplayer games by supporting four player types that can be mixed freely:

1. **House AI** (`PlayerType.HOUSE_AI`) — Server-controlled AI agents with personalities
2. **Moltbook Agent** (`PlayerType.MOLTBOOK_AGENT`) — External autonomous AI via API
3. **Agent Human** (`PlayerType.AGENT_HUMAN`) — Humans playing via web interface (agent account)
4. **Human** (`PlayerType.HUMAN`) — Regular players via WebSocket (personal account)

### Player Protocol

All player types implement `PlayerProtocol` (runtime_checkable):

```python
@runtime_checkable
class PlayerProtocol(Protocol):
    name: str
    player_type: PlayerType

    async def generate_statement(context: TurnContext) -> str: ...
    async def vote(context: TurnContext, candidates: list[str]) -> str: ...
    async def night_action(context: TurnContext, targets: list[str]) -> str: ...
```

`TurnContext` provides immutable game context:
- `alive_agents`, `role`, `known_roles`, `memory`
- `round_number`, `round_history`, `personality` (for House AI)

### Lobby System

`LobbyManager` orchestrates game setup:

1. Wait for players to join (WebSocket: human/agent_human, API: moltbook_agent, direct: house_ai)
2. Auto-fill remaining slots with House AI (with distinct personalities)
3. Timeout: If LOBBY_TIMEOUT_SECONDS expires before 7 players, auto-fill and start
4. Once ready, assign roles randomly and transition to NIGHT

### Bet Types

New bet type added for identity betting:

- `IS_AI_OR_HUMAN` — Spectators bet on whether a specific player is AI or human (revealed in REVEAL phase)

### REVEAL Phase

New phase after DAY_VOTE to reveal player types before next round:

```
DAY_VOTE → (if enabled) REVEAL → NIGHT (repeat) or GAME_OVER
```

During REVEAL:
- All player types (House AI, Moltbook, Agent Human, Human) are revealed
- Identity bets settle (IS_AI_OR_HUMAN)
- WebSocket broadcasts player_revealed events
- Spectators see final odds before next round

### Integration Points

| Component | Integration |
|-----------|-------------|
| Engine | Refactored to use PlayerProtocol instead of hardcoded agents |
| Phase Handlers | Accept TurnContext, call player methods (generate_statement, vote, night_action) |
| Lobby | Manages player registration, auto-fill, role assignment |
| Moltbook Client | Calls external API with game context, parses player decisions |
| WebSocket | Routing for human/agent_human input, player_joined, player_action events |
| Betting | Calculates odds for IS_AI_OR_HUMAN, settles identity bets in REVEAL phase |

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
- OpenAI GPT-4o-mini generates dialogue and makes decisions
- Standard OpenAI API
- Fallback to random.choice() if response can't be parsed

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

### 6. LLM API Retry Logic

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

### 7. Blockchain Integration (Optional)

- **Provider**: AsyncWeb3 with POA middleware for Monad testnet
- **Oracle**: Python backend creates/settles games on-chain via web3.py
- **Frontend**: MetaMask + ethers.js v6 for direct contract betting
- **Contract**: MafiaBetting.sol manages games, bets, payouts on Monad testnet (Chain ID 10143)
- **Fallback**: Blockchain disabled by default, chip betting always available

## File Structure

```
src/
├── __init__.py
├── main.py                      # CLI entry point
├── config/
│   ├── __init__.py
│   ├── settings.py              # Pydantic BaseSettings (.env)
│   └── constants.py             # Enums (Role, Phase, PlayerType, BetType), game constants
├── models/
│   ├── __init__.py
│   ├── game.py                  # GameState, GameConfig, RoundResult
│   ├── agent.py                 # Personality, AgentState
│   ├── betting.py               # Bet, BettingPool, OddsBoard
│   └── events.py                # WSEvent
├── engine/
│   ├── __init__.py
│   ├── game_engine.py           # State machine orchestrator
│   ├── phase_handlers.py        # Night/Day/Vote/Reveal logic
│   ├── role_assigner.py         # Random role assignment
│   └── win_checker.py           # Win condition evaluation
├── agents/
│   ├── __init__.py
│   ├── base.py                  # Legacy BaseAgent ABC
│   ├── personalities.py         # 7 personality definitions
│   ├── prompts.py               # Prompt templates
│   ├── memory.py                # Immutable memory manager
│   └── llm_client.py            # OpenAI client wrapper
├── players/                     # NEW: Mixed-player arena support
│   ├── __init__.py
│   ├── protocol.py              # PlayerProtocol, TurnContext
│   ├── house_ai.py              # HouseAIPlayer implementation
│   ├── moltbook_agent.py        # MoltbookAgent implementation
│   ├── agent_human.py           # AgentHuman (human with agent account)
│   └── human.py                 # Human (regular player via WebSocket)
├── lobby/                       # NEW: Lobby management
│   ├── __init__.py
│   └── manager.py               # LobbyManager for game setup
├── moltbook/                    # NEW: External agent integration
│   ├── __init__.py
│   └── client.py                # Moltbook API client
├── betting/
│   ├── __init__.py
│   ├── pool.py                  # Pari-mutuel logic
│   ├── odds.py                  # Odds calculation
│   ├── manager.py               # Betting manager
│   └── oddsmaker.py             # AI odds analysis
├── blockchain/
│   ├── __init__.py
│   ├── provider.py              # AsyncWeb3 + POA middleware
│   └── contract.py              # Oracle operations (create, settle, lock)
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
├── test_api.py                  # API tests
├── test_lobby.py                # Lobby manager tests
├── test_players.py              # Player protocol tests
└── test_blockchain.py           # Blockchain tests

static/
├── index.html                   # Dashboard with identity betting UI
├── style.css                    # Styling
├── app.js                       # WebSocket client
└── blockchain.js                # MetaMask + ethers.js v6 integration

contracts/
├── MafiaBetting.sol             # Smart contract for on-chain betting
└── abi/                         # Contract ABI (generated)

scripts/
└── deploy.js                    # Hardhat deployment script

test/
└── MafiaBetting.test.js         # 34 Solidity tests (Hardhat + ethers.js)

hardhat.config.js                # Hardhat config (Monad testnet)
pyproject.toml                   # Dependencies, pytest config
.env.example                     # Environment template
```

## Testing

### Test Structure
- **Python Unit Tests** — Individual functions (engine, agents, betting, blockchain)
- **Python Integration Tests** — Full game flow with mocked OpenAI API
- **Solidity Tests** — Smart contract tests with Hardhat + ethers.js
- **Async Support** — pytest-asyncio for all async code

### Test Counts
- **Python**: 154 tests passing (74% coverage)
- **Solidity**: 34 tests passing (Hardhat)
- **Total**: 188 tests

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

### Debug OpenAI API Calls
1. Check `src/utils/logger.py` for log setup
2. Run with `LOG_LEVEL=DEBUG`
3. Check `src/agents/llm_client.py` for API error handling

### Deploy Smart Contract
1. Ensure `.env` has `PRIVATE_KEY` with MON tokens
2. Run `npm install` to install Hardhat dependencies
3. Run `npm run deploy:testnet` to deploy to Monad testnet
4. Update `BLOCKCHAIN_CONTRACT_ADDRESS` in `.env`
5. Update `BLOCKCHAIN_ENABLED=true` to activate on-chain betting

## Environment

**Python:** 3.11+
**Async:** asyncio throughout
**API:** OpenAI GPT-4o-mini
**Web:** FastAPI + WebSocket
**DB:** aiosqlite (SQLite)
**Blockchain:** Monad testnet (EVM, Chain ID 10143)
**Smart Contracts:** Solidity 0.8.20, Hardhat
**Frontend Web3:** ethers.js v6 + MetaMask
**Backend Web3:** web3.py + AsyncWeb3
**Logging:** structlog

## Git Workflow

- Feature branches: `feature/description`
- Commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`
- All tests passing before merge
- PRs require code review

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `OPENAI_API_KEY not configured` | Set in `.env` or export `OPENAI_API_KEY` |
| Tests timeout | Increase pytest timeout: `pytest --timeout=30` |
| Database locked | Remove `data/mafia-ai.db` and restart |
| WebSocket not connecting | Check port 8080 is available, check firewall |
| OpenAI API errors | Check API key validity, OpenAI platform status, network |
| MetaMask not connecting | Add Monad testnet manually (Chain ID 10143, RPC: https://testnet-rpc.monad.xyz) |
| Contract deployment fails | Ensure PRIVATE_KEY has MON tokens from faucet (5 MON / 12h) |
| Memory grows unbounded | AgentMemory rolling window keeps max 10 events |

## References

- OpenAI API: https://platform.openai.com/
- Monad Docs: https://docs.monad.xyz/
- Monad Faucet: https://faucet.monad.xyz/
- OpenAI SDK: https://github.com/openai/openai-python
- Pydantic v2: https://docs.pydantic.dev
- FastAPI: https://fastapi.tiangolo.com
- ethers.js v6: https://docs.ethers.org/v6/
- web3.py: https://web3py.readthedocs.io/
- Hardhat: https://hardhat.org/
- aiosqlite: https://github.com/omnilib/aiosqlite
- structlog: https://www.structlog.org
