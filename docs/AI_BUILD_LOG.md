# AI Build Log — MafiaAI

> How AI was used to build an AI game, from architecture to deployment.

---

## Overview

MafiaAI was built almost entirely with AI assistance over an **8-day sprint (Feb 11-18, 2026)**. Two types of AI were used:

1. **Claude Code (Opus + Sonnet)** — Development tool for planning, implementation, testing, and documentation
2. **OpenAI GPT-4o-mini** — Production AI powering all 7 game agent personalities, odds analysis, and autonomous betting

---

## Development AI: Claude Code

### Agent Teams Pipeline

Every major feature was implemented using a **3-agent parallel pipeline**:

```
P0 Design (Opus)     → Architecture, file ownership map, API contracts
P1 Implementation    → 2-3 Sonnet agents building in parallel (file ownership enforced)
P2 Verification      → Hypothesis-based adversarial testing
P3 Refactoring       → Only if P2 found failures
```

**Why this matters**: Each pipeline phase produces artifacts (`docs/pipeline/*.md`) that the next phase consumes. Agents can't modify files outside their ownership boundary, preventing merge conflicts. The lead (Opus) never touches code — only plans and coordinates.

### Pipeline Timeline

| Day | Feature | Pipeline | Tests | Coverage |
|-----|---------|----------|:-----:|:--------:|
| 1 | Terminal game engine | P0→P1→P2 | 45 | 47% |
| 2 | WebSocket + dashboard | P1→P2 | 45 | 47% |
| 3 | Betting integration | P1→P2 | 45 | 47% |
| 4 | Tests + polish | P1→P2 | 82 | 66% |
| 5 | Blockchain (Monad) | P0→P1→P2→P3 | 125 | 68% |
| 6 | Mixed-Player Arena | P0→P1→P2→P3 | 188 | 73% |
| 7 | USDC unification + React rewrite | P0→P1→P2 | 275→398 | 72%→80% |
| 8 | V2 contracts + coverage push | P1→P2 | 520 | 89% |
| 9 | Refactoring + spectator chat + BSC deploy | Direct | 482 | 84% |

### AI-Generated Code Statistics

- **40+ source modules** (Python backend)
- **48 TypeScript files** (React frontend)
- **3 Solidity contracts** (V1, V2, MockERC20)
- **482 tests** (392 Python + 90 Solidity)
- **84% Python test coverage**
- **0 TypeScript errors** (strict mode)

### Key AI Development Decisions

1. **LLM swap (Day 5)** — Pipeline agent swapped Claude Haiku → OpenAI GPT-4o-mini in one phase, zero test regressions
2. **Frontend rewrite (Day 7)** — 3 agents rebuilt entire frontend from vanilla HTML/CSS/JS to React 19 + TypeScript + Tailwind in a single pipeline run
3. **V2 contract (Day 8)** — Agent designed commit-reveal betting contract with 4 bet types, oracle settlement, and pull-payment pattern. 56 tests generated.
4. **Coverage push (Day 8)** — Test writer agent pushed coverage from 80% → 89% by identifying untested paths in game_engine.py (18%→99%), storage (0%→100%), ws_manager (62%→100%)

---

## Production AI: GPT-4o-mini

### 7 AI Personalities

Each agent has a personality that shapes every LLM call:

| Agent | Trait | System Prompt Behavior |
|-------|-------|----------------------|
| Viktor | Strategist | Formal language, evidence-based accusations, calculated voting |
| Luna | Empath | Warm tone, defends newcomers, trusts easily |
| Rex | Bully | Aggressive accusations, dominates discussions |
| Sage | Philosopher | Measured analysis, weighs both sides |
| Nova | Wildcard | Unpredictable votes, chaotic reasoning |
| Iris | Observer | Quiet but analytical, pattern recognition |
| Blaze | Hothead | Snap judgments, emotional reactions |

### AI Operations Per Game

| Operation | Model | Calls/Game | Cost/Game |
|-----------|-------|:----------:|:---------:|
| Generate statement | GPT-4o-mini | ~42 (7 agents × 2 statements × 3 rounds) | ~$0.02 |
| Vote decision | GPT-4o-mini | ~21 (7 agents × 3 rounds) | ~$0.005 |
| Night action | GPT-4o-mini | ~9 (mafia + detective × 3 rounds) | ~$0.002 |
| Odds analysis | GPT-4o-mini | ~6 (after each phase) | ~$0.003 |
| AI Bettor analysis | GPT-4o-mini | ~4 (during betting windows) | ~$0.002 |
| **Total** | | **~82 calls** | **~$0.03** |

### AI Bettor (Autonomous On-Chain Agent)

The AI Bettor is a fully autonomous agent that:
1. Watches games via WebSocket (receives all game events)
2. Builds a `GameObservation` from event history
3. Sends observation to GPT-4o-mini for analysis
4. Receives structured `BetDecision` (bet_type, target, confidence, amount)
5. If confidence > 0.6, places USDC bet on-chain via X402 payment

This is a production AI agent that autonomously executes on-chain transactions based on real-time LLM analysis.

---

## AI-Assisted Testing

### Test Generation Strategy

The test writer agent was given specific coverage targets:

```
Module                    Before    After
game_engine.py            18%  →    99%
storage/database.py        0%  →   100%
utils/errors.py            0%  →   100%
utils/retry.py            52%  →   100%
api/ws_manager.py         62%  →   100%
```

For each module, the agent:
1. Read the source code to identify all branches
2. Generated test cases covering happy path, error paths, and edge cases
3. Used `pytest-asyncio` for all async code
4. Verified each test actually exercises the target code path

### Solidity Test Generation

The contract test agent generated **90 Hardhat tests** covering:
- V1: 34 tests (game creation, betting, settlement, edge cases)
- V2: 56 tests (commit-reveal, 4 bet types, oracle settlement, refund deadline, pull-payment)

All tests use ethers.js v6 fixtures with deterministic test accounts.

---

## Development Tools

| Tool | Role | Usage |
|------|------|-------|
| **Claude Code** | Development IDE | All planning, implementation, testing, documentation |
| **Claude Opus** | Architect | P0 design phases, file ownership maps, API contracts |
| **Claude Sonnet** | Implementer | P1 code generation, P2 verification, P3 refactoring |
| **Claude Haiku** | Reviewer | P0.5 security/performance reviews, P4 documentation |
| **OpenAI GPT-4o-mini** | Production AI | All 7 agent personalities, odds analysis, autonomous betting |
| **Hardhat** | Smart contracts | Compile, test, deploy Solidity contracts |
| **pytest** | Python testing | 430 tests with coverage reporting |

---

## Pipeline Artifacts

All pipeline documents are preserved in `docs/pipeline/`:

```
docs/pipeline/
├── PROGRESS.md          — Full timeline of all pipeline runs
├── DESIGN.md            — P0 architecture (game engine, agents, state machine)
├── PLAN.md              — Implementation plan with file ownership map
├── QA_REPORT.md         — P2 verification results
├── SMART_CONTRACT.md    — V2 contract design
├── USDC_DESIGN.md       — USDC unification architecture
├── X402_PLAN.md         — X402 payment integration design
└── [35 more files]      — Phase-specific implementation and review docs
```

---

## Summary

MafiaAI demonstrates AI at two levels:

1. **AI as builder** — Claude Code's agent teams pipeline produced 482 tests at 84% coverage in 9 days, with parallel implementation and adversarial verification
2. **AI as product** — 7 GPT-4o-mini agents play autonomous social deduction games while an AI Bettor executes on-chain bets and 3 AI commentators provide live spectator chat, creating a fully AI-driven gaming platform

The result: a production-ready AI social deduction arena built by AI, powered by AI, with on-chain execution on BSC and Monad testnets.
