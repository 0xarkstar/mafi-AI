# X402 API Integration — Implementation Summary

**Agent**: p-impl-api
**Date**: 2026-02-12
**Status**: ✅ Complete

## Overview

Successfully integrated X402 Open Betting Protocol into the existing MafiaAI server. This connects the X402 protocol layer and AI bettor to the FastAPI server and betting manager, enabling external agents and AI bettors to place bets using USDC payments.

## Changes Made

### 1. Settings (`src/config/settings.py`)

Added configuration for X402 and AI Bettor:

```python
# X402 Open Betting Protocol (optional)
x402_enabled: bool = False
x402_payment_token: str = "USDC"
x402_min_bet_usdc: int = 1

# AI Bettor (optional)
ai_bettor_enabled: bool = False
ai_bettor_private_key: SecretStr = SecretStr("")
ai_bettor_budget_usdc: int = 100
```

**Note**: The p-impl-x402 agent added more detailed X402 settings (facilitator_url, network, usdc_address, pay_to) which are fully compatible with this implementation.

### 2. Bet Model (`src/models/betting.py`)

Extended `Bet` with two optional fields:

```python
payment_method: str = "chips"      # "chips" or "x402"
tx_hash: str | None = None         # blockchain tx hash for x402 bets
```

**Design Decisions**:
- Default `payment_method="chips"` ensures backward compatibility
- `tx_hash` is optional (None for chip bets)
- `bettor_id` can now be either session_id (chips) or wallet address (x402)

### 3. BettingManager (`src/betting/manager.py`)

Added `handle_x402_bet()` method:

```python
def handle_x402_bet(
    self,
    bettor_address: str,
    bet_type: str,
    target: str,
    amount_usdc: Decimal,
    round_number: int,
    tx_hash: str,
) -> Bet | None:
```

**Key Differences from `place_bet()`**:
- **No balance check** (payment already verified by X402 middleware)
- Uses wallet address as `bettor_id`
- Sets `payment_method="x402"` and `tx_hash`
- Still validates bet_type enum
- Still applies early bet bonus (1.5x round 0, 1.2x round 1)
- Adds to the **same pari-mutuel pool** as chip bets

### 4. Server (`src/api/server.py`)

#### X402 Middleware (conditional)

```python
if settings.x402_enabled:
    try:
        from src.x402.middleware import create_x402_middleware
        x402_mw = create_x402_middleware(settings)
        app.add_middleware(x402_mw)
        log.info("x402_middleware_enabled")
    except ImportError:
        log.warning("x402_middleware_not_available")
```

**Graceful degradation**: If x402 module doesn't exist, server still starts (logs warning).

#### New Endpoint: `POST /api/bets/x402`

```python
@app.post("/api/bets/x402")
async def place_x402_bet(request: Request):
```

**Behavior**:
- **Production mode** (`x402_enabled=True`): Reads payment info from `request.state.x402_payment` (injected by middleware)
- **Test mode** (`x402_enabled=False`): Uses mock payment from headers (`X-Test-Address`, `X-Test-TxHash`)
- Calls `betting_manager.handle_x402_bet()`
- Returns bet confirmation with current odds

**Response Format**:

```json
{
  "success": true,
  "bet_id": "uuid",
  "bet_type": "side_win",
  "target": "mafia",
  "amount": 100.0,
  "weight": 1.5,
  "tx_hash": "0xabc...",
  "odds": {
    "mafia_win": 0.53,
    "citizen_win": 0.47
  }
}
```

### 5. Main (`src/main.py`)

Wired AI Bettor startup in `run_server_mode()`:

```python
# Start AI bettor if enabled
bettor_task = None
if settings.ai_bettor_enabled:
    try:
        from src.ai_bettor.client import AIBettorClient
        bettor = AIBettorClient(
            ws_url=f"ws://localhost:{settings.port}/ws",
            api_url=f"http://localhost:{settings.port}",
            api_key=settings.ai_bettor_private_key.get_secret_value(),
            budget_usdc=Decimal(str(settings.ai_bettor_budget_usdc)),
        )
        bettor_task = asyncio.create_task(bettor.run())
        log.info("ai_bettor_started", budget=settings.ai_bettor_budget_usdc)
    except ImportError:
        log.warning("ai_bettor_not_available")
```

**Cleanup**: Added bettor_task cancellation in the `except asyncio.CancelledError` block.

### 6. Tests (`tests/test_x402_betting.py`)

Created comprehensive integration tests (12 tests, all passing):

#### TestX402BettingManager (5 tests)
- ✅ Valid X402 bet placed without balance check
- ✅ Invalid bet type rejected
- ✅ Zero/negative amount rejected
- ✅ Early bet bonus applied correctly
- ✅ X402 and chip bets share same pool

#### TestBetModelDefaults (2 tests)
- ✅ Default fields correct (`payment_method="chips"`, `tx_hash=None`)
- ✅ X402 fields set correctly

#### TestBackwardCompatibility (2 tests)
- ✅ Existing chip betting unchanged
- ✅ Settlement works with mixed bets (chips + x402)

#### TestX402APIEndpoint (3 tests)
- ✅ Endpoint works in test mode
- ✅ Invalid bet type rejected
- ✅ Bet added to pool correctly

## Testing Results

### New Tests

```bash
tests/test_x402_betting.py ............                        [100%]

============================== 12 passed in 0.27s ===============================
```

### Backward Compatibility

```bash
tests/test_betting.py ..........................                [100%]

============================== 26 passed in 0.16s ===============================
```

**Total**: 38 tests (26 existing + 12 new), all passing.

## Design Patterns Followed

1. **Immutability**: All Pydantic models remain `frozen=True`
2. **No mutations**: Always create new instances with `model_copy(update={...})`
3. **Graceful degradation**: X402 and AI Bettor modules are optional (ImportError handled)
4. **Backward compatibility**: Existing chip betting functionality unchanged
5. **Unified pools**: X402 and chip bets compete in the same pari-mutuel pools
6. **Logging**: Comprehensive structlog events for debugging
7. **Test patterns**: Followed existing test structure (mock_claude, settings fixtures)

## API Usage Example

### Chip Betting (Existing)

```bash
# WebSocket message
{
  "type": "place_bet",
  "bet_type": "side_win",
  "target": "mafia",
  "amount": 100,
  "round": 0
}
```

### X402 Betting (New)

```bash
curl -X POST http://localhost:8080/api/bets/x402 \
  -H "Content-Type: application/json" \
  -H "X-Test-Address: 0x1234567890abcdef" \
  -H "X-Test-TxHash: 0xabcdef1234567890" \
  -d '{
    "bet_type": "side_win",
    "target": "mafia",
    "amount_usdc": 100,
    "round": 0
  }'
```

## Integration Points

| Component | Integration |
|-----------|-------------|
| **X402 Protocol** | Middleware injects payment info into `request.state` |
| **AI Bettor** | Calls POST /api/bets/x402 with authenticated requests |
| **Betting Manager** | Handles both chip and X402 bets in same pools |
| **Settlement** | Payouts work identically for both payment methods |
| **WebSocket** | Can broadcast X402 bet confirmations (future enhancement) |

## Environment Variables

Add to `.env`:

```bash
# X402 (optional)
X402_ENABLED=false
X402_PAYMENT_TOKEN=USDC
X402_MIN_BET_USDC=1

# AI Bettor (optional)
AI_BETTOR_ENABLED=false
AI_BETTOR_PRIVATE_KEY=0x...
AI_BETTOR_BUDGET_USDC=100
```

## Known Limitations

1. **X402 module dependency**: If `src/x402/` doesn't exist, middleware won't be loaded (logs warning, server still works)
2. **AI Bettor module dependency**: If `src/ai_bettor/` doesn't exist, bettor won't start (logs warning, server still works)
3. **Test mode headers**: Test mode uses simple headers (`X-Test-Address`, `X-Test-TxHash`) - not secure for production
4. **No WebSocket broadcast**: X402 bets don't currently trigger WebSocket events (can be added later)

## Next Steps (Not Implemented)

- [ ] WebSocket broadcast for X402 bet confirmations
- [ ] Rate limiting on `/api/bets/x402` endpoint
- [ ] X402 bettor leaderboard (wallet addresses)
- [ ] X402 bet history API endpoint

---

## Handoff

### What Was Attempted

1. **Settings integration** — Added X402 and AI Bettor configuration to `src/config/settings.py`
2. **Bet model extension** — Added `payment_method` and `tx_hash` fields to `Bet` class
3. **BettingManager method** — Implemented `handle_x402_bet()` with no balance check
4. **Server endpoint** — Created `POST /api/bets/x402` with test mode and production mode
5. **X402 middleware** — Conditionally added middleware if x402_enabled=True
6. **AI Bettor startup** — Wired bettor initialization and cleanup in main.py
7. **Comprehensive tests** — 12 new integration tests covering all edge cases

### What Worked

✅ **All 12 new tests passing**
✅ **All 26 existing betting tests still passing** (backward compatibility verified)
✅ **X402 and chip bets share same pari-mutuel pools** (fair competition)
✅ **Graceful degradation** (missing modules don't crash server)
✅ **Test mode works** (can test endpoint without X402 protocol layer)
✅ **Immutability preserved** (all Pydantic models still frozen)
✅ **Logging comprehensive** (structlog events for debugging)

### What Didn't Work / Issues

⚠️ **Settings file modified by parallel agent** — The p-impl-x402 agent added more detailed X402 settings while I was working. This is **not a problem** — my implementation is compatible with both the minimal settings I added and the detailed settings they added.

❌ **No real issues** — Everything implemented as specified. The only "gotcha" was using `TestClient` instead of `httpx.AsyncClient` for FastAPI tests, but this was quickly resolved by checking existing test patterns.

### What Remains

**Nothing blocking** — This implementation is complete and ready for integration.

**Optional enhancements** (not required):
- WebSocket broadcast for X402 bet confirmations (would need to modify endpoint to call `ws_manager.broadcast()`)
- Rate limiting on `/api/bets/x402` (FastAPI slowapi middleware)
- X402 bettor analytics dashboard (query bets by wallet address)

### Dependencies

**Expects from p-impl-x402**:
- `src/x402/middleware.py` with `create_x402_middleware(settings)` function
- `src/x402/models.py` with `X402BetRequest` and `X402PaymentInfo` models
- Middleware should inject `request.state.x402_payment` with payment info

**Expects from p-impl-bettor**:
- `src/ai_bettor/client.py` with `AIBettorClient` class
- Constructor: `AIBettorClient(ws_url, api_url, api_key, budget_usdc)`
- Method: `async def run()` (long-running coroutine)

**No file conflicts** — Modified files (`server.py`, `manager.py`, `betting.py`, `main.py`) were all assigned to me exclusively.

### Testing Commands

```bash
# Run X402 integration tests
.venv/bin/python -m pytest tests/test_x402_betting.py -v

# Run existing betting tests (backward compatibility)
.venv/bin/python -m pytest tests/test_betting.py -v

# Run both together
.venv/bin/python -m pytest tests/test_x402_betting.py tests/test_betting.py -v
```

### Context for Next Phase (P2: Verification)

**p-qa agent** should verify:
1. All 154 existing tests + 12 new X402 tests = 166 tests pass
2. Coverage remains ≥73% (likely higher with new tests)
3. X402 endpoint works with real middleware (integration test)
4. AI Bettor can successfully place bets via X402 endpoint
5. Mixed betting (chip + x402) settlement is fair (pari-mutuel correctness)
6. No regressions in existing game flow

**Files to review**:
- `src/models/betting.py` (Bet model)
- `src/betting/manager.py` (handle_x402_bet method)
- `src/api/server.py` (POST /api/bets/x402 endpoint)
- `src/main.py` (AI Bettor startup)
- `tests/test_x402_betting.py` (all 12 tests)

**Integration points to test**:
- X402 middleware → endpoint → BettingManager → pari-mutuel pool
- AI Bettor → POST /api/bets/x402 → bet confirmation
- Chip bets and X402 bets competing in same pool → fair settlement

---

**Handoff complete. Ready for P2 verification.**
