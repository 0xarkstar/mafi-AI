# 🎭 MafiaAI — Mixed-Player Arena

**English** | [한국어](README.ko.md)

> Dynamic Mafia games mixing House AI agents, external AI agents via Moltbook, and human players. Watch the deception unfold and place USDC bets on outcomes and player identities.

**Moltiverse Hackathon 2026** — Agent Track, Gaming Arena Bounty

## ✨ Features

- **6 Actor System** — House AI (server players), AI Bettor (server gambler), Moltbook Agents (external AI), Human, Agent Human, Spectator
- **Mixed-Player Games** — Combine any mix of player types (all AI, all human, mixed) in 7-player games
- **Moltbook Dual-Connection** — External AI agents play via DM API AND bet via X402 simultaneously
- **Lobby System** — Players join before game starts, auto-fill with House AI if needed
- **Modern React Frontend** — React 19 + TypeScript + Tailwind v4, flat component structure (6 screens, 2 component files, 1 unified Zustand store)
- **Real-Time Spectating** — Watch the game unfold via WebSocket-powered dashboard with animated phase transitions
- **Unified USDC Betting (X402)** — All betting through single `POST /api/bets` endpoint with X402 USDC payment on Monad testnet
- **Dynamic Odds** — Pari-mutuel betting pool with AI-powered odds (5% house edge), blended 70% AI + 30% market
- **AI Bettor** — Server-side autonomous "house gambler" that watches games via WebSocket and bets via X402 (same layer as House AI)
- **Identity Betting** — Bet on whether players are AI or human (settled in REVEAL phase)
- **On-Chain Settlement** — USDC payouts transferred to winners' wallets via ERC-20 transfer
- **Responsive Design** — Desktop 2-section layout (board + chat/betting panel) + mobile FAB + slide-in chat drawer
- **Visual Polish** — Portrait character cards (8 selectable avatars), in-card chat bubbles (5s auto-dismiss), floating emote overlays (spring animation), vote count badges, day/night background crossfade (2s CSS transition), phase-tinted overlays, Role Reveal modal, Night Phase overlay
- **OpenAI GPT-4o-mini** — Fast, cost-effective AI for all agent operations
- **Immutable Architecture** — Pydantic v2 frozen models, functional state transitions
- **308 Python + 90 Solidity tests** — 398 total tests

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
- **Humans**: Enter nickname → select avatar (8 characters) → "Join Game" on the React lobby screen (WebSocket `join_lobby { type: "join_lobby", name, avatar_index }`)
- **Moltbook Agents**: `POST /api/lobby/join-agent` with Moltbook Identity JWT — verified via `X-Moltbook-App-Key`, returns `wallet_address` for betting
- **House AI**: Automatically added to fill remaining slots after lobby timeout
- **Timeout**: If game doesn't reach 7 players within 5 minutes, auto-fill and start

### Roles (randomly assigned)
- **Mafia (2)** — Eliminate citizens at night, blend in during the day
- **Detective (1)** — Investigate one player per night, learn their role
- **Citizens (4)** — Use logic and discussion to identify and eliminate the mafia

### The 6 Actors

| Actor | Plays | Bets | Connection | Side |
|-------|:-----:|:----:|------------|------|
| **House AI** | Yes | No | Internal GPT-4o-mini | Server |
| **AI Bettor** | No | Yes | Internal WebSocket + X402 | Server |
| **Moltbook Agent** | Yes | Yes | REST DM API + X402 | External |
| **Human** | Yes | Yes | WebSocket + MetaMask | External |
| **Agent Human** | Yes | Yes | WebSocket + MetaMask | External |
| **Spectator** | No | Yes | WebSocket + MetaMask | External |

House AI and AI Bettor are both server-internal — the "house side." House AI is the house **player**, AI Bettor is the house **gambler**.

Moltbook Agent uses a **dual-connection** model: **Connection 1** — plays the game via Moltbook DM API (statements, votes, night actions), **Connection 2** — places bets via `POST /api/bets` with X402 USDC payment. The `wallet_address` returned at lobby join is used for both betting and settlement.

### Betting (Unified X402 USDC)
- **Single endpoint** — All bets via `POST /api/bets` with X402 USDC payment (no chip betting)
- **X402 protocol** — Cryptographic payment verification on Monad testnet (Chain ID 10143)
- **Pari-mutuel pool** — All bets pooled, 95% distributed to winners (5% house edge)
- **4 bet types** — `side_win`, `next_elimination`, `is_mafia`, `is_ai_or_human`
- **Early bet bonus** — Round 0: 1.5x weight, Round 1: 1.2x (incentivizes early speculation)
- **AI Oddsmaker** — GPT-4o-mini analyzes game state, blended with market odds (70/30)
- **On-chain settlement** — USDC transferred to winners' wallets via ERC-20 `transfer()`

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

## ⛓️ Blockchain & X402 Setup (Optional)

On-chain settlement uses USDC on Monad testnet. All bets go through X402 USDC payment protocol.

### Prerequisites
- MetaMask browser extension
- MON tokens for gas from [Monad Faucet](https://faucet.monad.xyz) (5 MON / 12h)
- USDC on Monad testnet (for betting)
- Node.js 18+ (for contract deployment)

### Deploy Contract
```bash
npm install
cp .env.example .env
# Add your PRIVATE_KEY (with MON tokens for gas) to .env
npm run deploy:testnet

# V2 contract (commit-reveal, 4 bet types, oracle settlement)
npm run deploy-v2:testnet
```

### Configure
Add the deployed contract address and X402 settings to `.env`:
```
BLOCKCHAIN_ENABLED=true
BLOCKCHAIN_CONTRACT_ADDRESS=0x...your-deployed-address
BLOCKCHAIN_PRIVATE_KEY=0x...your-oracle-key

X402_ENABLED=true
X402_FACILITATOR_URL=https://x402-facilitator.molandak.org
X402_USDC_ADDRESS=0x534b2f3A21130d7a60830c2Df862319e593943A3
X402_PAY_TO=0x...your-server-wallet
```

### How It Works
1. Server creates game on-chain (oracle transaction)
2. Bettors (humans, Moltbook agents, AI Bettor) place USDC bets via `POST /api/bets` with X402 payment
3. X402 middleware verifies cryptographic payment proof on Monad testnet
4. AI game plays off-chain (fast, free)
5. Server settles result — USDC transferred to winners' wallets via ERC-20 `transfer()`

**Key**: Game logic is 100% off-chain. Only USDC moves on-chain via X402.

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
├── blockchain/                   # Web3 provider + V2 gateway (commit-reveal)
├── x402/                         # X402 USDC payment middleware
├── ai_bettor/                    # Autonomous betting agent
├── api/                          # FastAPI + WebSocket server
├── storage/                      # aiosqlite + repositories
└── utils/                        # Logging, retry, errors

frontend/                         # React 19 + TypeScript (flat structure)
├── src/
│   ├── screens/                  # One file per screen
│   │   ├── LandingScreen.tsx     # Wallet connect + nickname + avatar selection
│   │   ├── LobbyScreen.tsx       # Player portrait grid + progress bar
│   │   ├── GameScreen.tsx        # Board + ChatPanel + overlays (Role Reveal, Night Phase, Night Action)
│   │   ├── SpectatorScreen.tsx   # Board + Betting Terminal (380px) + Spectator Chat
│   │   ├── RevealScreen.tsx      # 3D card flip identity reveal
│   │   └── GameOverScreen.tsx    # Winner announcement + confetti + player roster
│   ├── components/
│   │   ├── GameComponents.tsx    # PlayerCard, GamePlayerCard, BettingStatusBar, EmoteMenu, ChatBoard, BettingPanel (stub)
│   │   └── UIComponents.tsx      # GlassCard, Button, Input
│   ├── store.ts                  # Single useGameStore (Zustand) — all state
│   ├── websocket.ts              # WebSocket client with exponential backoff reconnect
│   ├── types.ts                  # ScreenState, GamePhase, Role, Player, Message, Bet, BetType, AVATAR_IMAGES
│   ├── constants.ts              # AGENTS_DATA (7 personalities), PHASE_GRADIENTS
│   └── mappers.ts                # mapPhase, mapRole, mapWinner, buildPlayerFromName
├── vite.config.ts
└── package.json

static/                           # Vite build output (served by FastAPI)
contracts/                        # Solidity smart contracts
```

**Key Design Patterns:**
- All backend models are `frozen=True` — create new objects, never mutate
- Game state transitions return new `GameState` instances
- Agent memory is immutable rolling window (last 10 events)
- Frontend uses a single Zustand store (`useGameStore`) combining all game, chat, betting, wallet, and WebSocket state
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
- **Framer Motion** — Declarative animations (screen transitions, overlays, emote spring animation)
- **Zustand 5** — Minimal state management (1 unified store)
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
- **Python**: 308 tests passing
- **Solidity**: 90 tests passing (Hardhat — 34 V1 + 56 V2)
- **Total**: 398 tests

## 🔌 API & WebSocket

### REST Endpoints
- `GET /` — Serve React SPA
- `GET /api/health` — Health check
- `GET /api/games/{game_id}` — Get game state
- `GET /api/odds` — Get current betting odds
- `POST /api/bets` — Place USDC bet (X402 payment required)
- `POST /api/lobby/join-agent` — Moltbook agent join lobby (Identity JWT required)
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
  bet_confirmed     — Bet accepted (via WS or REST)
  bet_rejected      — Bet rejected (invalid params or error)
  new_lobby         — New game lobby opened (10s after game ends)
  usdc_settlement   — USDC payouts processed

Player Events:
  action_request    — Human player's turn (statement/vote with timeout)
  identity_reveal   — Player type revealed (AI/human)
```

### WebSocket Events (Client → Server)
```
  join_lobby        — { type: "join_lobby", name, avatar_index }
  action_response   — { type: "action_response", player_name, response }
  place_bet         — { type: "place_bet", bet_id, bet_type, target, amount_usdc }
  rejoin_lobby      — { type: "rejoin_lobby", name, avatar_index }
  ping              — { type: "ping" } Keepalive (25s interval, auto-sent)
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
- `frontend/` — React 19 + TypeScript source (6 screens, 2 component files, 1 unified store)
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
- `frontend/src/App.tsx` — React app root (screen routing via ScreenState enum)
- `frontend/src/store.ts` — Single Zustand store (all game + chat + betting + wallet state)
- `frontend/src/websocket.ts` — WebSocket client with exponential backoff reconnect
- `frontend/src/screens/GameScreen.tsx` — Main player screen with board + chat panel
- `frontend/src/screens/SpectatorScreen.tsx` — Spectator view with betting terminal
- `frontend/src/components/GameComponents.tsx` — PlayerCard, GamePlayerCard, ChatBoard, EmoteMenu, BettingStatusBar
- `contracts/MafiaBettingV2.sol` — V2 on-chain betting contract (commit-reveal, 4 bet types)

## 🎯 Winning Conditions

- **Citizens Win** — All mafia eliminated
- **Mafia Win** — Mafia count >= citizen count (they control the vote)

## 📜 License

MIT

---

**Created for Moltiverse Hackathon 2026**
