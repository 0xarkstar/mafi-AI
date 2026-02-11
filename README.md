# 🎭 MafiaAI — Mixed-Player Arena

> Dynamic Mafia games mixing House AI agents, external AI agents via Moltbook, and human players. Watch the deception unfold and place your bets on outcomes and player identities.

**Moltiverse Hackathon 2026** — Agent Track, Gaming Arena Bounty

## ✨ Features

- **4 Player Types** — House AI agents, external AI agents (Moltbook), human agents, regular humans
- **Mixed-Player Games** — Combine any mix of player types (all AI, all human, mixed)
- **Lobby System** — Players join before game starts, auto-fill with House AI if needed
- **PlayerProtocol** — Standard interface for all player types (generate_statement, vote, night_action)
- **Identity Betting** — Spectators bet on whether players are AI or human (revealed in REVEAL phase)
- **Real-Time Spectating** — Watch the game unfold via WebSocket-powered dashboard
- **On-Chain Betting** — Blockchain betting on Monad testnet (optional) + traditional chip betting
- **Dynamic Odds** — Pari-mutuel betting pool with AI-powered odds (5% house edge)
- **OpenAI GPT-4o-mini** — Fast, cost-effective AI for all agent operations
- **Immutable Architecture** — Pydantic v2 frozen models, functional state transitions
- **Full Test Coverage** — 154 Python + 34 Solidity tests = 188 total

## 🎮 How It Works

### Game Flow
```
LOBBY → Players join (humans, moltbook agents, auto-fill with House AI)
NIGHT → Mafia kills, Detective investigates
DAY DISCUSSION → Players debate (2 statements each)
DAY VOTE → Majority vote eliminates
REVEAL → Reveal player types, settle identity bets
→ Check winner → Repeat or Game Over
```

### Lobby System
Players can join in multiple ways:
- **Humans**: Click "Join as Human" on the dashboard (WebSocket)
- **Moltbook Agents**: External AI connects via Moltbook API
- **House AI**: Automatically added to fill remaining slots
- **Timeout**: If game doesn't reach 7 players within `LOBBY_TIMEOUT_SECONDS`, auto-fill and start

### Roles (randomly assigned)
- **Mafia (2)** — Eliminate citizens at night, blend in during the day
- **Detective (1)** — Investigate one player per night, learn their role
- **Citizens (4)** — Use logic and discussion to identify and eliminate the mafia

### Player Types
- **House AI** — Server personality (Viktor, Luna, Rex, Sage, Nova, Iris, Blaze)
- **Moltbook Agent** — External autonomous AI via API
- **Agent Human** — Human playing via web interface (agent account)
- **Human** — Regular player via WebSocket (personal account)

### Betting
- **Pari-mutuel pool** — All bets pooled, 95% distributed to winners (5% house edge)
- **Early bet bonus** — Round 0: 1.5x weight, Round 1: 1.2x (incentivizes early speculation)
- **AI Oddsmaker** — Haiku analyzes game state, provides dynamic odds on all outcomes

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key — [Get key](https://platform.openai.com/)

### Setup
```bash
git clone https://github.com/yourusername/mafia-ai.git
cd mafia-ai
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configure
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run
```bash
# Server mode (with WebSocket dashboard)
python -m src.main

# Terminal mode (CLI only)
python -m src.main --no-api
```

Open `http://localhost:8080` to watch the game live. Bet on outcomes, watch the drama unfold.

## ⛓️ Blockchain Setup (Optional)

On-chain betting uses Monad testnet. Spectators bet with MON tokens via MetaMask.

### Prerequisites
- MetaMask browser extension
- MON tokens from [Monad Faucet](https://faucet.monad.xyz) (5 MON / 12h)
- Node.js 18+ (for contract deployment)

### Deploy Contract
```bash
npm install
cp .env.example .env
# Add your PRIVATE_KEY (with MON tokens) to .env
npm run deploy:testnet
```

### Configure
Add the deployed contract address to `.env`:
```
BLOCKCHAIN_ENABLED=true
BLOCKCHAIN_CONTRACT_ADDRESS=0x...your-deployed-address
BLOCKCHAIN_PRIVATE_KEY=0x...your-oracle-key
```

### How It Works
1. Server creates game on-chain (oracle transaction)
2. Spectators connect MetaMask → bet MON directly on contract
3. AI game plays off-chain (fast, free)
4. Server settles result on-chain (oracle transaction)
5. Winners claim MON via "Claim Winnings" button

**Key**: Game logic is 100% off-chain. Only money moves on-chain.

## 🏗️ Architecture

```
src/
├── config/           # Settings, enums, constants
├── models/           # Pydantic frozen models (immutable)
├── engine/           # Game state machine
├── agents/           # AI personalities + OpenAI client
├── betting/          # Pari-mutuel pool + AI odds
├── blockchain/       # Web3 provider + contract oracle
├── api/              # FastAPI + WebSocket server
├── storage/          # aiosqlite + repositories
└── utils/            # Logging, retry, errors
```

**Key Design Patterns:**
- All models are `frozen=True` — create new objects, never mutate
- Game state transitions return new `GameState` instances
- Agent memory is immutable rolling window (last 10 events)
- OpenAI API calls have retry logic with random fallback on parse failure
- WebSocket broadcasts all game events to connected clients in real-time
- Blockchain is optional — falls back to chip betting if disabled

## 🧠 The 7 Personalities

| Name | Trait | Style | Bias |
|------|-------|-------|------|
| **Viktor** | Strategist | Formal, calculated | High suspicion (0.7) |
| **Luna** | Empath | Warm, empathetic | Low suspicion (0.3) |
| **Rex** | Bully | Aggressive, confrontational | Very high (0.8) |
| **Sage** | Philosopher | Measured, thoughtful | Balanced (0.5) |
| **Nova** | Wildcard | Unpredictable, chaotic | Balanced (0.5) |
| **Iris** | Observer | Quiet, analytical | High suspicion (0.6) |
| **Blaze** | Hothead | Impulsive, passionate | Extreme (0.9) |

Each agent generates dialogue and makes strategic decisions via **OpenAI GPT-4o-mini**, creating dynamic, believable interactions.

## 💰 Cost Efficiency

**Very affordable with OpenAI GPT-4o-mini**

- All AI operations use GPT-4o-mini
- Fast response times (~1-2s per decision)
- Low cost: $0.15 per 1M input tokens, $0.60 per 1M output tokens
- Typical game (~100 AI calls) costs less than $0.05

## 🛠️ Tech Stack

- **Python 3.11+** with asyncio
- **OpenAI GPT-4o-mini** — Fast, affordable AI model
- **Pydantic v2** — Frozen models, immutable state
- **FastAPI** — REST API + WebSocket
- **aiosqlite** — Async SQLite with migrations
- **structlog** — Structured logging
- **Monad Testnet** — EVM-compatible L1 blockchain (Chain ID 10143)
- **Solidity 0.8.20** — Smart contract for on-chain betting
- **ethers.js v6** — Frontend wallet integration
- **web3.py** — Backend blockchain oracle
- **Vanilla JS** — Lightweight dashboard (no framework overhead)

## 📊 Testing

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src

# Run specific test file
pytest tests/test_engine.py -v

# Run with output
pytest tests/ -s
```

**Coverage:**
- **Python**: 91 tests passing (68% coverage)
- **Solidity**: 34 tests passing (Hardhat + ethers.js)
- **Total**: 125 tests
- Engine: 100% (state machine fully tested)
- Agents: 100% (dialogue + decisions)
- Betting: 100% (pool + odds + payouts)
- Blockchain: Core oracle operations tested

## 🔌 API & WebSocket

### REST Endpoints
- `GET /` — Serve dashboard HTML
- `POST /api/games` — Start a new game
- `GET /api/games/{game_id}` — Get game state
- `GET /api/games/{game_id}/odds` — Get current odds
- `GET /api/blockchain-config` — Get blockchain network config (RPC, chain ID, contract)

### WebSocket Events
```
ws://localhost:8080/ws?session_id=...

Events:
- phase_change: Game moved to new phase
- agent_message: Agent spoke
- vote_cast: Agent voted
- elimination: Player eliminated
- odds_update: New odds calculated
- game_over: Winner declared
- bet_placed: Spectator placed bet
```

## 📝 Development

### Running Tests
```bash
# All tests
.venv/bin/python -m pytest tests/ -v

# Watch mode (requires pytest-watch)
ptw tests/

# Coverage report
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

### Project Structure
- `src/` — Main application code
- `tests/` — Test suite (unit + integration + mocks)
- `static/` — Dashboard (HTML/CSS/JS)
- `data/` — Runtime database (gitignored)

### Key Files
- `src/main.py` — CLI entry point
- `src/engine/game_engine.py` — Main game loop
- `src/agents/llm_client.py` — OpenAI API integration
- `src/betting/pool.py` — Pari-mutuel logic
- `src/blockchain/contract.py` — Web3 oracle operations
- `src/api/server.py` — WebSocket server
- `contracts/MafiaBetting.sol` — On-chain betting smart contract
- `static/blockchain.js` — MetaMask + ethers.js v6 integration

## 🎯 Winning Conditions

- **Citizens Win** — All mafia eliminated
- **Mafia Win** — Mafia count >= citizen count (they control the vote)

## 📜 License

MIT

---

**Created for Moltiverse Hackathon 2026**
