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

X402 Open Betting variables (optional - for USDC betting):
- `X402_ENABLED=false`
- `X402_FACILITATOR_URL=https://x402-facilitator.molandak.org`
- `X402_NETWORK=eip155:10143` (Monad testnet)
- `X402_USDC_ADDRESS=0x534b2f3A21130d7a60830c2Df862319e593943A3`
- `X402_PAY_TO=0xyour-server-wallet`

AI Bettor variables (optional - for autonomous betting):
- `AI_BETTOR_ENABLED=false`
- `AI_BETTOR_PRIVATE_KEY=0xyour-private-key` (optional for future on-chain settlement)
- `AI_BETTOR_BUDGET_USDC=50.0` (starting USDC budget)

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
| `src/blockchain/` | Web3 provider, V2 gateway (commit-reveal, lock, settle), contract ABIs |
| `src/x402/` | X402 payment middleware, USDC bet models, payment verification |
| `src/ai_bettor/` | AI Bettor client, game analyzer, betting strategy, immutable state |
| `src/api/` | FastAPI server, WebSocket manager, REST routes, blockchain config endpoint |
| `src/api/validators.py` | Request validation (Pydantic schemas) |
| `src/api/bet_routes.py` | Betting REST endpoints (extracted from routes.py) |
| `src/api/lobby_routes.py` | Lobby REST endpoints (extracted from routes.py) |
| `src/api/ws_handler.py` | WebSocket message handler (extracted from server.py) |
| `src/utils/` | Logging (structlog), retry logic |

### Game Flow

```
1. LOBBY: Players join (humans via WebSocket, external agents via Moltbook, house AI auto-fills)
   - Wait for 7 players or timeout, then auto-fill with House AI
2. (Optional) V2: `commit_roles()` — commit role hash on-chain with secret
3. NIGHT: Mafia kills, Detective investigates (OpenAI or human/agent input)
4. DAY_DISCUSSION: Each player makes 2 statements (OpenAI/Moltbook/human input)
5. DAY_VOTE: Each player votes (OpenAI/Moltbook/human input)
6. Check winner:
   - Citizens win if all mafia dead
   - Mafia wins if mafia >= citizens
   - Otherwise repeat from NIGHT
7. GAME_OVER: Announce winner
   - (Optional) V2: `lock_betting()` → `settle_game()` (commit-reveal on-chain)
   - (Legacy) Direct USDC push via `USDCSettlement` if no V2 gateway
8. REVEAL: Show player identities, settle identity bets
9. BettingManager.reset() between games in continuous game loop
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
wallet_address: str | None

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

## X402 Open Betting Protocol

### Overview

X402 enables optional open betting using USDC on Monad testnet via the X402 micropayment protocol. Unlike chip-based betting (always available), X402 betting allows users to place real USDC bets with cryptographic payment verification.

**Dual Betting System**: Spectators can place bets using either:
1. **Chip Betting** (default) — In-game chips, unlimited, pari-mutuel pool
2. **USDC Betting via X402** (optional) — Real USDC payments, 1.0 USDC minimum, verified on-chain

### X402 Payment Flow

```
1. Spectator initiates X402 bet via POST /api/bets/x402
2. Middleware checks x-payment header
3. If missing → return 402 Payment Required with payment requirements
4. Spectator pays via X402 facilitator (cryptographic proof)
5. Middleware verifies payment signature
6. Extract payer address, amount, tx_hash
7. Settle payment (mark as claimed on facilitator)
8. Proceed with bet placement
```

### Endpoints

**POST /api/bets/x402** — Place a bet with USDC payment (X402 protected)

Request (with x-payment header from X402 facilitator):
```json
{
  "game_id": "game-123",
  "bet_type": "side_win",
  "target": "citizens",
  "amount_usdc": 1.5,
  "round_number": 0
}
```

Response (200 OK):
```json
{
  "bet_id": "bet-456",
  "game_id": "game-123",
  "bet_type": "side_win",
  "target": "citizens",
  "amount_usdc": 1.5,
  "payer_address": "0x742d...",
  "tx_hash": "0xabcd..."
}
```

### Configuration

X402 environment variables (optional, default: disabled):
- `X402_ENABLED=false` — Enable X402 USDC betting
- `X402_FACILITATOR_URL=https://x402-facilitator.molandak.org` — X402 facilitator endpoint
- `X402_NETWORK=eip155:10143` — Monad testnet network ID
- `X402_USDC_ADDRESS=0x534b2f3A...` — USDC token contract on Monad
- `X402_PAY_TO=0x...` — Server wallet receiving USDC payments

### Implementation

- **Middleware**: `src/x402/middleware.py` — Enforces X402 payment, verifies signatures
- **Models**: `src/x402/models.py` — X402BetRequest, X402PaymentInfo (frozen Pydantic)
- **Integration**: Attaches `request.state.x402_payment` with payer info to verified requests

## AI Bettor (Autonomous Betting Agent)

### Overview

AI Bettor is an autonomous WebSocket client that watches live games and places strategic USDC bets via X402. It combines LLM-based game analysis with deterministic betting strategy to maximize expected value.

**Core Features**:
- Listens to all game events via WebSocket (game_started, phase_change, odds_update, elimination, etc.)
- Analyzes current game state using GPT-4o-mini
- Places bets during high-confidence opportunities
- Enforces betting strategy (cooldown, phase restrictions, confidence threshold)
- Tracks balance, bets placed, total wagered/won

### Module Structure

| Module | Purpose |
|--------|---------|
| `analyzer.py` | LLM-based GameAnalyzer — generates BetDecision from GameObservation |
| `strategy.py` | Deterministic BettingStrategy — timing, cooldown, confidence → amount mapping |
| `client.py` | AIBettorClient — main orchestrator, WebSocket listener, bet placer |
| `models.py` | Frozen Pydantic models (GameObservation, BetDecision, AIBettorState) |

### Betting Strategy

**Phases**: Bets only during `day_discussion` and `day_vote` phases

**Cooldown**: Minimum 30 seconds between bets (prevents rapid fire)

**Confidence Threshold**: Minimum 0.6 (60% confidence) to place bet

**Amount Scaling**: Linear mapping from confidence → amount
- Confidence 0.6 → $1.00 USDC
- Confidence 1.0 → $10.00 USDC
- Formula: `amount = $1 + ($9 × (confidence - 0.6) / 0.4)`

**Balance Protection**: Bet amount capped at available balance

### Game Analysis (LLM)

GameAnalyzer uses OpenAI GPT-4o-mini to evaluate:
- Current phase and round number
- Alive vs dead agents
- Recent events (last 10)
- Current odds board
- Available balance

Response format parsed by analyzer:
```
bet: yes/no
bet_type: side_win | is_mafia | next_elimination | is_ai_or_human
target: <target>
amount: <1.00-10.00>
confidence: <0.0-1.0>
reasoning: <one line>
```

### Configuration

AI Bettor environment variables (optional, default: disabled):
- `AI_BETTOR_ENABLED=false` — Enable autonomous betting agent
- `AI_BETTOR_PRIVATE_KEY=...` — Optional private key for on-chain settlement
- `AI_BETTOR_BUDGET_USDC=50.0` — Starting budget in USDC

### State Management

AIBettorState (immutable, frozen):
```python
balance_usdc: Decimal         # Remaining balance
bets_placed: int              # Total bets made
last_bet_time: float | None   # Timestamp of last bet
total_wagered: Decimal        # Cumulative amount wagered
total_won: Decimal            # Cumulative winnings
```

State transitions are immutable:
```python
self.state = self.state.model_copy(
    update={
        "balance_usdc": new_balance,
        "bets_placed": new_count,
        "last_bet_time": time.time(),
    }
)
```

### Usage

```python
from src.ai_bettor.client import AIBettorClient
from decimal import Decimal

bettor = AIBettorClient(
    ws_url="ws://localhost:8080/ws",
    api_url="http://localhost:8080",
    api_key="sk-...",
    budget_usdc=Decimal("50.00"),
)

# Run until stop() is called
await bettor.run()

# Stop gracefully
await bettor.stop()
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
- **Gateway**: `BlockchainGateway` handles V2 commit-reveal lifecycle (commit_roles → lock_betting → settle_game)
- **V2 Contract**: `MafiaBettingV2.sol` — bytes32 gameId, 4 bet types, oracle settlement, pull-payment (`claimPayout`)
- **Frontend**: MetaMask + ethers.js v6 for direct contract betting
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
│   ├── phase_handlers.py        # Re-export shim for backward compat
│   ├── phase_night.py           # Night phase handler
│   ├── phase_day.py             # Day discussion phase handler
│   ├── phase_vote.py            # Day vote phase handler
│   ├── role_assigner.py         # Random role assignment
│   └── win_checker.py           # Win condition evaluation
├── agents/
│   ├── __init__.py
│   ├── personalities.py         # 7 personality definitions
│   ├── prompts.py               # Prompt templates
│   ├── memory.py                # Immutable memory manager
│   └── llm_client.py            # OpenAI client wrapper
├── players/
│   ├── __init__.py
│   ├── protocol.py              # PlayerProtocol, TurnContext
│   ├── house_ai.py              # HouseAIPlayer implementation
│   ├── moltbook_agent.py        # MoltbookAgent implementation
│   └── human.py                 # HumanPlayer + AgentHumanPlayer
├── lobby/                       # NEW: Lobby management
│   ├── __init__.py
│   └── manager.py               # LobbyManager for game setup
├── cli/
│   ├── __init__.py
│   └── terminal.py              # Terminal mode CLI (print_event, run_terminal_mode)
├── moltbook/                    # NEW: External agent integration
│   ├── __init__.py
│   └── client.py                # Moltbook API client
├── betting/
│   ├── __init__.py
│   ├── pool.py                  # Pari-mutuel logic
│   ├── odds.py                  # Odds calculation
│   ├── manager.py               # Betting manager
│   ├── oddsmaker.py             # AI odds analysis
│   └── settlement.py            # USDCSettlement (legacy direct USDC push)
├── blockchain/
│   ├── __init__.py
│   ├── provider.py              # AsyncWeb3 + POA middleware
│   └── gateway.py               # V2 BlockchainGateway (commit-reveal, lock, settle)
├── x402/
│   ├── __init__.py
│   ├── middleware.py            # X402 payment middleware (402 Payment Required)
│   └── models.py                # X402BetRequest, X402PaymentInfo (frozen)
├── ai_bettor/
│   ├── __init__.py
│   ├── client.py                # AIBettorClient (main WebSocket orchestrator)
│   ├── analyzer.py              # GameAnalyzer (LLM-based decision maker)
│   ├── strategy.py              # BettingStrategy (deterministic rules)
│   └── models.py                # GameObservation, BetDecision, AIBettorState (frozen)
├── api/
│   ├── __init__.py
│   ├── server.py                # FastAPI app factory + static files (90 lines)
│   ├── routes.py                # Game REST endpoints
│   ├── bet_routes.py            # Betting REST endpoints
│   ├── lobby_routes.py          # Lobby REST endpoints
│   ├── ws_handler.py            # WebSocket message handler
│   ├── ws_manager.py            # WebSocket broadcast
│   └── validators.py            # Request validation schemas
└── utils/
    ├── __init__.py
    ├── logger.py                # structlog setup
    └── retry.py                 # async retry decorator

tests/
├── __init__.py
├── conftest.py                  # pytest fixtures
├── test_engine.py               # Game engine + V2 lifecycle tests
├── test_agents.py               # Agent tests
├── test_betting.py              # Betting tests
├── test_api.py                  # API endpoint tests
├── test_lobby.py                # Lobby manager tests
├── test_players.py              # Player protocol + wallet_address tests
├── test_blockchain.py           # Blockchain provider + contract tests
├── test_gateway.py              # BlockchainGateway + helper function tests
├── test_settlement.py           # USDCSettlement tests
├── test_moltbook.py             # Moltbook client tests
├── test_x402.py                 # X402 middleware and payment tests
├── test_x402_betting.py         # X402 betting integration tests
├── test_ai_bettor.py            # AI Bettor client, analyzer, strategy tests
├── test_validators.py           # Request validation tests
├── test_bet_routes.py           # Betting endpoint tests
├── test_lobby_routes.py         # Lobby endpoint tests
└── test_ws_handler.py           # WebSocket handler tests

frontend/                        # React + TypeScript frontend (Vite)
├── src/
│   ├── App.tsx                  # Main app with routing
│   ├── components/
│   │   ├── shared/              # Reusable: GameBackground, GameHeader, PhaseIndicator, PlayerGrid
│   │   ├── BettingPanel.tsx     # Betting sidebar (extracted from SpectatorScreen)
│   │   ├── SpecChatPanel.tsx    # Spectator chat (extracted from SpectatorScreen)
│   │   ├── NightOverlay.tsx     # Night phase overlay (extracted from GameScreen)
│   │   ├── NightActionPanel.tsx # Night action UI (extracted from GameScreen)
│   │   ├── RoleRevealModal.tsx  # Role reveal modal (extracted from GameScreen)
│   │   ├── ErrorBoundary.tsx    # React error boundary
│   │   ├── GameComponents.tsx   # BettingStatusBar, etc.
│   │   ├── GamePlayerCard.tsx   # Player card with avatar, emotes
│   │   ├── ChatBoard.tsx        # Chat panel
│   │   └── UIComponents.tsx     # GlassCard, Button, Input
│   ├── screens/                 # SpectatorScreen, GameScreen, LandingScreen, etc.
│   ├── store/                   # Zustand slices: gameSlice, bettingSlice, connectionSlice, uiSlice
│   ├── hooks/                   # useChatBubbles, useCountdown, useNightOverlay, useActionTimeout
│   ├── types/
│   │   ├── index.ts             # Core types (Player, Message, GamePhase, etc.)
│   │   └── events.ts            # ServerEvent union type
│   ├── mappers.ts               # Server→client data mappers
│   ├── constants.ts             # Avatar data, agent configs
│   ├── constants/
│   │   └── timing.ts            # Shared timing constants (TIMING)
│   └── websocket.ts             # WebSocket connection manager
└── static/                      # Compiled: index.html, assets/, images/

contracts/
├── MafiaBetting.sol             # V1 smart contract (legacy)
├── MafiaBettingV2.sol           # V2: commit-reveal, 4 bet types, pull-payment, refund deadline
└── MockERC20.sol                # Test token for Hardhat tests

scripts/
├── deploy.js                    # V1 Hardhat deployment script
└── deploy-v2.js                 # V2 Hardhat deployment script

test/
├── MafiaBetting.test.js         # 34 V1 Solidity tests (Hardhat + ethers.js)
└── MafiaBettingV2.test.js       # 56 V2 Solidity tests (commit-reveal, 4 bet types)

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
- **Python**: 392 tests passing
- **Solidity**: 90 tests passing (Hardhat — 34 V1 + 56 V2)
- **Total**: 482 tests
- **Coverage**: 84%

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
