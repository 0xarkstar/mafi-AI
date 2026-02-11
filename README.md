# 🎭 MafiaAI — AI Agents Play Mafia, You Bet on the Outcome

> 7 AI agents with distinct personalities play Mafia in real-time. Watch the deception unfold and place your bets on who survives.

**Moltiverse Hackathon 2026** — Agent Track, Gaming Arena Bounty

## ✨ Features

- **7 Unique AI Personalities** — Viktor (strategist), Luna (empath), Rex (bully), Sage (philosopher), Nova (wildcard), Iris (observer), Blaze (hothead)
- **Real-Time Spectating** — Watch the game unfold via WebSocket-powered dashboard
- **Dynamic Betting** — Pari-mutuel betting pool with AI-powered odds (5% house edge)
- **Two AI Models** — Haiku 4.5 for fast dialogue, Sonnet 4.5 for strategic decisions
- **Immutable Architecture** — Pydantic v2 frozen models, functional state transitions
- **Full Test Coverage** — 45+ tests with pytest, pytest-asyncio, and coverage tracking

## 🎮 How It Works

### Game Flow
```
NIGHT → Mafia kills, Detective investigates
DAY DISCUSSION → Agents debate (2 statements each)
DAY VOTE → Majority vote eliminates
→ Check winner → Repeat or Game Over
```

### Roles
- **Mafia (2)** — Eliminate citizens at night, blend in during the day
- **Detective (1)** — Investigate one player per night, learn their role
- **Citizens (4)** — Use logic and discussion to identify and eliminate the mafia

### Betting
- **Pari-mutuel pool** — All bets pooled, 95% distributed to winners (5% house edge)
- **Early bet bonus** — Round 0: 1.5x weight, Round 1: 1.2x (incentivizes early speculation)
- **AI Oddsmaker** — Haiku analyzes game state, provides dynamic odds on all outcomes

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key

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
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run
```bash
# Server mode (with WebSocket dashboard)
python -m src.main

# Terminal mode (CLI only)
python -m src.main --no-api
```

Open `http://localhost:8080` to watch the game live. Bet on outcomes, watch the drama unfold.

## 🏗️ Architecture

```
src/
├── config/           # Settings, enums, constants
├── models/           # Pydantic frozen models (immutable)
├── engine/           # Game state machine
├── agents/           # AI personalities + Claude API client
├── betting/          # Pari-mutuel pool + AI odds
├── api/              # FastAPI + WebSocket server
├── storage/          # aiosqlite + repositories
└── utils/            # Logging, retry, errors
```

**Key Design Patterns:**
- All models are `frozen=True` — create new objects, never mutate
- Game state transitions return new `GameState` instances
- Agent memory is immutable rolling window (last 10 events)
- Claude API calls have retry logic with random fallback on parse failure
- WebSocket broadcasts all game events to connected clients in real-time

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

Each agent generates dialogue via **Haiku 4.5** and makes strategic decisions via **Sonnet 4.5**, creating dynamic, believable interactions.

## 💰 Cost Efficiency

**~$0.18 per game** (~550 games per $100 API credit)

- Dialogue generation: Haiku 4.5 (fast, cheap)
- Strategic decisions: Sonnet 4.5 (accurate, slightly pricier)
- Odds analysis: Haiku 4.5 (fast market analysis)

## 🛠️ Tech Stack

- **Python 3.11+** with asyncio
- **Claude API** (Haiku 4.5 + Sonnet 4.5)
- **Pydantic v2** — Frozen models, immutable state
- **FastAPI** — REST API + WebSocket
- **aiosqlite** — Async SQLite with migrations
- **structlog** — Structured logging
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
- Engine: 100% (state machine fully tested)
- Agents: 100% (dialogue + decisions)
- Betting: 100% (pool + odds + payouts)
- 45+ tests, pytest-asyncio for async support

## 🔌 API & WebSocket

### REST Endpoints
- `GET /` — Serve dashboard HTML
- `POST /api/games` — Start a new game
- `GET /api/games/{game_id}` — Get game state
- `GET /api/games/{game_id}/odds` — Get current odds

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
- `src/agents/claude_client.py` — API integration
- `src/betting/pool.py` — Pari-mutuel logic
- `src/api/server.py` — WebSocket server

## 🎯 Winning Conditions

- **Citizens Win** — All mafia eliminated
- **Mafia Win** — Mafia count >= citizen count (they control the vote)

## 📜 License

MIT

---

**Created for Moltiverse Hackathon 2026**
