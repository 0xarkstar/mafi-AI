# 🎭 MafiaAI — Mixed-Player Arena

**English** | [한국어](README.ko.md)

> Dynamic Mafia games mixing House AI agents, external AI agents via Moltbook, and human players. Watch the deception unfold and place USDC bets on outcomes and player identities.

**Moltiverse Hackathon 2026** — Agent Track, Gaming Arena Bounty

## ✨ Features

- **4 Player Types** — House AI agents, external AI agents (Moltbook), human agents, regular humans
- **Mixed-Player Games** — Combine any mix of player types (all AI, all human, mixed)
- **Lobby System** — Players join before game starts, auto-fill with House AI if needed
- **Modern React Frontend** — React 19 + TypeScript + Tailwind v4 + Framer Motion glassmorphism UI
- **Real-Time Spectating** — Watch the game unfold via WebSocket-powered dashboard with animated phase transitions
- **USDC Betting via X402** — On-chain USDC betting on Monad testnet with X402 micropayment protocol
- **Dynamic Odds** — Pari-mutuel betting pool with AI-powered odds (5% house edge)
- **AI Bettor** — Autonomous betting agent that analyzes games and places strategic USDC bets
- **Identity Betting** — Spectators bet on whether players are AI or human (revealed in REVEAL phase)
- **Responsive Design** — Desktop 3-column layout + mobile tabbed interface
- **Visual Polish** — Portrait character cards, in-card chat bubbles with gold border, floating emote overlays, vote badges, day/night background crossfade, phase-tinted overlays, role badge icons
- **OpenAI GPT-4o-mini** — Fast, cost-effective AI for all agent operations
- **Immutable Architecture** — Pydantic v2 frozen models, functional state transitions
- **236 Python + 39 Solidity tests** — 275 total tests

## 🎮 How It Works

### Game Flow

See [docs/USERFLOW.md](docs/USERFLOW.md) (English) | [docs/USERFLOW.ko.md](docs/USERFLOW.ko.md) (한국어) for detailed flow charts with Mermaid diagrams.

```
LOBBY → Players join (humans, moltbook agents, auto-fill with House AI)
  ↓
NIGHT → Mafia kills, Detective investigates
  ↓
DAY DISCUSSION → Players debate (2 statements each)
  ↓
DAY VOTE → Majority vote eliminates
  ↓
REVEAL → Reveal player types, settle identity bets
  ↓
Check winner → Citizens win (all mafia dead) / Mafia win (mafia ≥ citizens) / Repeat
```

### Game Modes

- **All-AI (Default)** — 7 House AI agents auto-play, spectators can watch and bet
- **Mixed** — Humans join via lobby, remaining slots auto-filled with House AI
- **Spectator** — Watch game + place bets via SpectatorScreen, no gameplay influence
- **External Agent** — Autonomous AI agents join via Moltbook API integration

### Lobby System
Players can join in multiple ways:
- **Humans**: Enter name and click "Join Game" on the React lobby screen (WebSocket)
- **Moltbook Agents**: External AI connects via Moltbook API
- **House AI**: Automatically added to fill remaining slots
- **Timeout**: If game doesn't reach 7 players within 5 minutes, auto-fill and start

### Roles (randomly assigned)
- **Mafia (2)** — Eliminate citizens at night, blend in during the day
- **Detective (1)** — Investigate one player per night, learn their role
- **Citizens (4)** — Use logic and discussion to identify and eliminate the mafia

### Player Types
- **House AI** — Server personality (Viktor, Luna, Rex, Sage, Nova, Iris, Blaze)
- **Moltbook Agent** — External autonomous AI via API
- **Agent Human** — Human playing via web interface (agent account)
- **Human** — Regular player via WebSocket (personal account)

### Betting (USDC via X402)
- **X402 micropayment protocol** — USDC bets on Monad testnet with cryptographic payment verification
- **Pari-mutuel pool** — All bets pooled, 95% distributed to winners (5% house edge)
- **Early bet bonus** — Round 0: 1.5x weight, Round 1: 1.2x (incentivizes early speculation)
- **AI Oddsmaker** — GPT-4o-mini analyzes game state, provides dynamic odds
- **AI Bettor** — Autonomous agent watches games and places strategic bets

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend build)
- OpenAI API key — [Get key](https://platform.openai.com/)

### Setup
```bash
git clone https://github.com/0xarkstar/mafi-AI.git
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

### Build Frontend
```bash
cd frontend
npm install
npm run build   # outputs to ../static/
cd ..
```

### Run
```bash
# Production mode (serves built React SPA)
python -m src.main

# Terminal mode (CLI only, no web UI)
python -m src.main --no-api
```

Open `http://localhost:8080` to play.

### Development Mode
```bash
# Terminal 1: Backend
python -m src.main

# Terminal 2: Frontend dev server (hot reload)
cd frontend && npm run dev
```

Vite dev server at `http://localhost:5173` proxies API/WebSocket to the backend at `:8080`.

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
src/                              # Python backend
├── config/                       # Settings, enums, constants
├── models/                       # Pydantic frozen models (immutable)
├── engine/                       # Game state machine
├── agents/                       # AI personalities + OpenAI client
├── players/                      # PlayerProtocol implementations (4 types)
├── lobby/                        # Lobby manager for game setup
├── moltbook/                     # External agent API client
├── betting/                      # Pari-mutuel pool + AI odds
├── blockchain/                   # Web3 provider + contract oracle
├── x402/                         # X402 USDC payment middleware
├── ai_bettor/                    # Autonomous betting agent
├── api/                          # FastAPI + WebSocket server
├── storage/                      # aiosqlite + repositories
└── utils/                        # Logging, retry, errors

frontend/                         # React 19 + TypeScript (54 source files)
├── src/
│   ├── components/
│   │   ├── layout/               # Header, GameLayout, MobileTabBar
│   │   ├── lobby/                # LobbyScreen, PlayerSlot, JoinForm
│   │   ├── game/                 # GameBoard, PlayerCard (portrait images, not CSS-art avatars), ChatPanel, PhaseOverlay, EmoteMenu, NightOverlay, BettingStatusBar, etc.
│   │   ├── betting/              # BettingPanel, OddsBar, BetSlip, SuspectList, etc.
│   │   ├── wallet/               # ConnectButton, TxToast
│   │   ├── screens/              # LandingScreen, SpectatorScreen, RevealScreen, GameOverScreen
│   │   └── ui/                   # GlassCard, Badge, Button, Confetti, Input, ProgressRing, RoleRevealModal, etc.
│   ├── hooks/                    # useWebSocket, useGameState, useWallet, etc.
│   ├── stores/                   # Zustand stores (game, chat, betting, wallet)
│   └── lib/                      # Types, constants, WebSocket client, blockchain
├── vite.config.ts
└── package.json

static/                           # Vite build output (served by FastAPI)
contracts/                        # Solidity smart contracts
```

**Key Design Patterns:**
- All backend models are `frozen=True` — create new objects, never mutate
- Game state transitions return new `GameState` instances
- Agent memory is immutable rolling window (last 10 events)
- Frontend uses Zustand 5 with individual selectors (React 19 compatible)
- WebSocket auto-reconnect with exponential backoff
- Phase-adaptive UI (background gradients, animated transitions per phase)
- Blockchain/X402 is optional — game works without wallet connection

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

### Backend
- **Python 3.11+** with asyncio
- **OpenAI GPT-4o-mini** — Fast, affordable AI model
- **Pydantic v2** — Frozen models, immutable state
- **FastAPI** — REST API + WebSocket
- **aiosqlite** — Async SQLite with migrations
- **structlog** — Structured logging
- **web3.py** — Backend blockchain oracle

### Frontend
- **React 19** + TypeScript — Component-based SPA
- **Vite 6** — Fast HMR, optimized builds
- **Tailwind CSS v4** — Utility-first styling
- **Framer Motion** — Declarative animations (phase transitions, stagger effects)
- **Zustand 5** — Minimal state management (4 stores)
- **Lucide React** — Icons
- **ethers.js v6** — MetaMask + contract interaction

### Blockchain
- **Monad Testnet** — EVM-compatible L1 (Chain ID 10143)
- **Solidity 0.8.20** — On-chain betting contract
- **X402 Protocol** — USDC micropayment verification

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
- **Python**: 236 tests passing
- **Solidity**: 39 tests passing (Hardhat + ethers.js)
- **Total**: 275 tests

## 🔌 API & WebSocket

### REST Endpoints
- `GET /` — Serve React SPA
- `POST /api/games` — Start a new game
- `GET /api/games/{game_id}` — Get game state
- `GET /api/games/{game_id}/odds` — Get current odds
- `POST /api/bets/x402` — Place USDC bet (X402 payment required)
- `GET /api/blockchain-config` — Get blockchain network config

### WebSocket Events (Server → Client)
```
ws://localhost:8080/ws

Game Events:
  phase_change      — Game moved to new phase (night, day_discussion, day_vote, reveal, game_over)
  agent_message     — AI agent spoke (name + message)
  vote_cast         — Player voted (voter + target)
  elimination       — Player eliminated (role reveal + reason)
  game_over         — Winner declared (mafia/citizens)

Lobby Events:
  lobby_joined      — Player successfully joined
  lobby_status      — Current lobby state (players list, count, ready)
  game_starting     — Lobby full, game about to begin

Betting Events:
  odds_update       — New odds calculated (mafia/citizen win prob + suspect rankings)
  bet_placed        — Bet confirmed
  bet_confirmed     — Bet won
  bet_rejected      — Bet lost
  usdc_settlement   — USDC payouts processed

Player Events:
  action_request    — Human player's turn (statement/vote with timeout)
  identity_reveal   — Player type revealed (AI/human)
```

### WebSocket Events (Client → Server)
```
  join_lobby        — { type, name }
  action_response   — { type, player_name, response }
  ping              — Keepalive (30s interval)
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
- `src/` — Python backend (API, game engine, AI agents, betting, blockchain)
- `frontend/` — React 19 + TypeScript source (54 source files)
- `static/` — Vite build output (served by FastAPI in production)
- `tests/` — Test suite (unit + integration + mocks)
- `contracts/` — Solidity smart contracts
- `docs/` — User flow documentation + diagrams
- `data/` — Runtime database (gitignored)

### Key Files
- `src/main.py` — CLI entry point
- `src/engine/game_engine.py` — Main game loop
- `src/agents/llm_client.py` — OpenAI API integration
- `src/betting/pool.py` — Pari-mutuel logic
- `src/x402/middleware.py` — X402 USDC payment verification
- `src/ai_bettor/client.py` — Autonomous betting agent
- `src/api/server.py` — FastAPI + WebSocket server
- `frontend/src/App.tsx` — React app root (routing, WS connection)
- `frontend/src/hooks/useWebSocket.ts` — 15+ WS event handlers
- `frontend/src/stores/gameStore.ts` — Zustand game state
- `contracts/MafiaBetting.sol` — On-chain betting smart contract

## 🎯 Winning Conditions

- **Citizens Win** — All mafia eliminated
- **Mafia Win** — Mafia count >= citizen count (they control the vote)

## 📜 License

MIT

---

**Created for Moltiverse Hackathon 2026**
