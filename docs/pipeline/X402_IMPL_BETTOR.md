# X402 Implementation: House AI Bettor

**Agent:** p-impl-bettor
**Phase:** P1 Implementation
**Status:** ✅ Complete
**Date:** 2026-02-12

## Overview

Implemented a complete, standalone House AI Bettor module that autonomously watches Mafia games via WebSocket and places strategic bets via the X402 REST API using LLM-based game analysis.

## Deliverables

### Created Files

1. **`src/ai_bettor/__init__.py`** — Module init
2. **`src/ai_bettor/models.py`** — Frozen Pydantic v2 models
   - `GameObservation` — Immutable game state snapshot
   - `BetDecision` — LLM betting decision
   - `AIBettorState` — Bettor state tracking
3. **`src/ai_bettor/strategy.py`** — Pure logic betting strategy
   - Phase-based betting (only day_discussion/day_vote)
   - 30-second cooldown enforcement
   - Confidence-based amount calculation ($1-$10, linear scaling)
   - Minimum confidence threshold (0.6)
4. **`src/ai_bettor/analyzer.py`** — LLM-based game analyzer
   - Uses OpenAI GPT-4o-mini for betting decisions
   - Structured prompt with game state, odds, events
   - Robust parsing with fallback to no-bet on errors
5. **`src/ai_bettor/client.py`** — Main orchestration client
   - WebSocket connection with retry logic
   - Event accumulation (rolling 10-event window)
   - Immutable state management
   - REST API integration for bet placement
6. **`tests/test_ai_bettor.py`** — Comprehensive test suite (30 tests)

### Test Results

```
tests/test_ai_bettor.py::test_game_observation_frozen PASSED             [  3%]
tests/test_ai_bettor.py::test_bet_decision_frozen PASSED                 [  6%]
tests/test_ai_bettor.py::test_ai_bettor_state_frozen PASSED              [ 10%]
tests/test_ai_bettor.py::test_strategy_should_bet_in_betting_phase PASSED [ 13%]
tests/test_ai_bettor.py::test_strategy_should_bet_in_day_vote_phase PASSED [ 16%]
tests/test_ai_bettor.py::test_strategy_should_not_bet_in_lobby PASSED    [ 20%]
tests/test_ai_bettor.py::test_strategy_should_not_bet_in_night PASSED    [ 23%]
tests/test_ai_bettor.py::test_strategy_should_not_bet_in_game_over PASSED [ 26%]
tests/test_ai_bettor.py::test_strategy_should_not_bet_in_reveal PASSED   [ 30%]
tests/test_ai_bettor.py::test_strategy_should_not_bet_with_zero_balance PASSED [ 33%]
tests/test_ai_bettor.py::test_strategy_cooldown_enforcement PASSED       [ 36%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_min_confidence PASSED [ 40%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_max_confidence PASSED [ 43%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_mid_confidence PASSED [ 46%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_below_threshold PASSED [ 50%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_exceeds_balance PASSED [ 53%]
tests/test_ai_bettor.py::test_strategy_calculate_amount_at_balance PASSED [ 56%]
tests/test_ai_bettor.py::test_analyzer_parse_valid_response PASSED       [ 60%]
tests/test_ai_bettor.py::test_analyzer_parse_no_bet PASSED               [ 63%]
tests/test_ai_bettor.py::test_analyzer_parse_malformed_returns_no_bet PASSED [ 66%]
tests/test_ai_bettor.py::test_analyzer_api_error_returns_no_bet PASSED   [ 70%]
tests/test_ai_bettor.py::test_analyzer_build_prompt PASSED               [ 73%]
tests/test_ai_bettor.py::test_client_build_observation PASSED            [ 76%]
tests/test_ai_bettor.py::test_client_build_observation_no_game PASSED    [ 80%]
tests/test_ai_bettor.py::test_client_reset_game_state PASSED             [ 83%]
tests/test_ai_bettor.py::test_client_add_event_rolling_window PASSED     [ 86%]
tests/test_ai_bettor.py::test_client_handle_game_started_event PASSED    [ 90%]
tests/test_ai_bettor.py::test_client_handle_elimination_event PASSED     [ 93%]
tests/test_ai_bettor.py::test_client_lifecycle PASSED                    [ 96%]
tests/test_ai_bettor.py::test_client_place_bet_updates_state PASSED      [100%]

============================== 30 passed in 0.23s
```

## Architecture

### Component Design

```
AIBettorClient (main orchestrator)
    ├── WebSocket Listener
    │   ├── Event accumulation (game_started, phase_change, odds_update, etc.)
    │   └── Build GameObservation from events
    │
    ├── GameAnalyzer (LLM-based)
    │   ├── Structured prompts to GPT-4o-mini
    │   ├── Parse betting decisions
    │   └── Graceful error handling (fallback to no-bet)
    │
    ├── BettingStrategy (pure logic)
    │   ├── Phase-based timing (day_discussion, day_vote only)
    │   ├── 30s cooldown enforcement
    │   ├── Confidence-based amount ($1-$10 linear)
    │   └── Budget management
    │
    └── REST API Client (httpx)
        └── POST /api/bets/x402
```

### Key Design Decisions

1. **Immutability Throughout**
   - All Pydantic models frozen (`frozen=True`)
   - State transitions create new instances
   - No mutation patterns anywhere

2. **Separation of Concerns**
   - `analyzer.py` — LLM decision-making only
   - `strategy.py` — Pure logic (timing, cooldown, amounts)
   - `client.py` — Orchestration and I/O
   - `models.py` — Data structures only

3. **Robust Error Handling**
   - WebSocket: retry with exponential backoff
   - LLM: return no-bet decision on parsing errors
   - REST API: log failures, don't crash

4. **Event Accumulation**
   - Rolling window of last 10 events
   - Builds complete game observation from partial WS events
   - Resets state on new game

5. **Strategic Betting**
   - Only bets during active phases (day_discussion, day_vote)
   - Skips LOBBY, NIGHT, REVEAL, GAME_OVER
   - Confidence threshold 0.6 minimum
   - Linear amount scaling: confidence 0.6 → $1, 1.0 → $10

## Usage Example

```python
from decimal import Decimal
from src.ai_bettor.client import AIBettorClient

client = AIBettorClient(
    ws_url="ws://localhost:8080/ws",
    api_url="http://localhost:8080",
    api_key="sk-...",
    budget_usdc=Decimal("100.00"),
)

# Run the bettor (blocks until stopped)
await client.run()
```

## Integration Points

### WebSocket Events Consumed

- `game_started` → Reset state, set alive_agents
- `phase_change` → Update phase, trigger bet consideration
- `odds_update` → Update odds board, trigger bet consideration
- `elimination` → Move agent from alive to dead
- `agent_message` → Add to recent events
- `vote` → Add to recent events
- `game_over` → Mark game complete

### REST API Called

- `POST /api/bets/x402` with payload:
  ```json
  {
    "game_id": "game123",
    "bet_type": "side_win",
    "target": "citizens",
    "amount": 5.50
  }
  ```

## LLM Prompt Structure

```
# Mafia Game Betting Analysis

## Game State
Phase: {phase} | Round: {round_number}
Alive: {alive_agents}
Dead: {dead_agents}

## Recent Events
{recent_events}

## Current Odds
{current_odds}

## Your Balance: {balance} USDC

## Decide
Respond in exactly this format:
bet: yes/no
bet_type: side_win | is_mafia | next_elimination | is_ai_or_human
target: <target>
amount: <1.00-10.00>
confidence: <0.0-1.0>
reasoning: <brief one line>
```

## Test Coverage

### Models (3 tests)
- ✅ GameObservation immutability
- ✅ BetDecision immutability
- ✅ AIBettorState immutability

### Strategy (14 tests)
- ✅ Phase-based betting (6 tests: day_discussion, day_vote, lobby, night, reveal, game_over)
- ✅ Balance checking
- ✅ Cooldown enforcement (30s)
- ✅ Amount calculation (6 tests: min/max/mid confidence, below threshold, exceeds balance, at balance)

### Analyzer (5 tests)
- ✅ Parse valid LLM response
- ✅ Parse "no" decision
- ✅ Handle malformed response (fallback to no-bet)
- ✅ Handle API error (fallback to no-bet)
- ✅ Build proper prompt

### Client (8 tests)
- ✅ Build observation from events
- ✅ Return None when no game_id
- ✅ Reset game state
- ✅ Rolling event window (max 10)
- ✅ Handle game_started event
- ✅ Handle elimination event
- ✅ Lifecycle (start/stop)
- ✅ State update after bet placement

## Dependencies

- `openai` — AsyncOpenAI client for LLM analysis
- `httpx` — Async HTTP client for REST API
- `websockets` — WebSocket client
- `pydantic` — Frozen models
- `structlog` — Logging (via `src.utils.logger`)

## Code Quality

- ✅ All Pydantic models frozen
- ✅ 100% immutable patterns
- ✅ Comprehensive error handling
- ✅ Async throughout
- ✅ Structured logging
- ✅ Type hints everywhere
- ✅ No code smells

## Files Modified

**None** — This is a completely standalone module with zero modifications to existing code.

---

## Handoff

### Attempted

1. **Model Design** — Created frozen Pydantic models for game observation, bet decision, and bettor state
2. **Strategy Logic** — Implemented pure logic for timing, cooldown, and confidence-based betting
3. **LLM Integration** — Built GameAnalyzer using OpenAI GPT-4o-mini with structured prompts
4. **Client Orchestration** — Developed AIBettorClient with WebSocket listening, event accumulation, and REST API integration
5. **Comprehensive Testing** — Wrote 30 tests covering all components

### Worked

- ✅ All 30 tests pass
- ✅ Immutable design throughout
- ✅ Clean separation of concerns
- ✅ Robust error handling (WS retry, LLM fallback, API error logging)
- ✅ Strategic betting logic (phase-based, cooldown, confidence threshold)
- ✅ Event accumulation with rolling window
- ✅ Standalone module (no existing file modifications)

### Failed

**None** — All requirements met, all tests pass.

### Remaining

1. **Integration with X402 API** — This module is complete but requires the X402 REST API endpoint (`POST /api/bets/x402`) to be implemented by p-impl-x402-server
2. **CLI Entry Point** — Optional: Add a standalone CLI script to run the bettor (e.g., `scripts/run_bettor.py`)
3. **Configuration** — Optional: Add config file support for WS URL, API URL, budget
4. **Multiple Strategies** — Future: Support pluggable strategy classes (aggressive, conservative, etc.)
5. **Performance Metrics** — Future: Track win rate, ROI, Sharpe ratio
6. **Live Dashboard** — Future: Real-time visualization of bettor state and decisions

### Notes for Next Phase

- The bettor is **fully functional** once the X402 API endpoint exists
- The module is **completely standalone** and can be tested independently with mocks
- Consider adding **integration tests** in P1.5 that test bettor + API together
- The LLM prompt can be **tuned** based on P2 verification results
- Current strategy is **conservative** (0.6 min confidence, 30s cooldown) — adjust if needed
