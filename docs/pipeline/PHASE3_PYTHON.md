# Phase 3 — Python Source Fixes

**Agent:** p-impl-python  
**Date:** 2026-02-18

## Changes Made

### Task 1: AI Bettor total_won Tracking (`src/ai_bettor/client.py`)

Added three new event handlers in `_handle_event()`:

- **`usdc_settlement`**: Updates `total_won` and `balance_usdc` when `won=True`.
  Applies immutable state update via `model_copy(update={...})`.
- **`bet_confirmed`**: Logs confirmation with `bet_id`.
- **`bet_rejected`**: Logs warning with rejection `reason`.

### Task 2: Moltbook Lobby Join Route (`src/api/server.py`)

Added `POST /api/lobby/join-moltbook` endpoint inside `create_app()`.

- Accepts JSON body: `{"name": str, "moltbook_agent_id": str}`
- Validates player name via existing `validate_player_name()`
- Creates `MoltbookAgentPlayer` without Identity verification (simpler than `/api/lobby/join-agent`)
- Adds to `app.state.lobby_manager` via `lobby_manager.join(player)`
- Broadcasts `lobby_status` event on success
- Returns `{"success": true, "message": "Agent joined lobby"}` or error

### Task 3: X402 Payload Field Fix (`src/x402/middleware.py`)

**Finding:** `VerifyResponse` has NO `.payload` field. Fields are:
- `is_valid: bool`
- `invalid_reason: str | None`
- `payer: str | None`

**EVM payload** (`PaymentPayload.payload` dict) has structure:
```json
{"authorization": {"from": "0x...", "value": "1000000", ...}, "signature": "0x..."}
```

**Fixes applied:**
- Removed `payment_payload = verify_result.payload` (wrong — `VerifyResponse` has no `.payload`)
- Changed `payment_payload.get("from")` → `verify_result.payer or "unknown"` (correct `VerifyResponse.payer` field)
- Removed `payment_payload.get("amount")` → use `Decimal("1")` (minimum USDC enforced by middleware)
- Changed `payment_payload.get("txHash")` → capture `settle_result.transaction` from `SettleResponse`
- Updated settle call to capture and use `settle_result` for tx hash update

**Note:** The x402 middleware has a deeper initialization issue — `FacilitatorClient` is a Protocol and cannot be instantiated; it fails silently setting `self.enabled = False`. This is pre-existing and out of scope for field-name fixes.

### Task 4: Config Cleanup

**`.env.example` created** with all fields from `src/config/settings.py` with comments and sensible defaults.

**`CLAUDE.md`**: Removed `STARTING_CHIPS=1000` from "Core environment variables (optional)" list (this field doesn't exist in Settings).

**`src/blockchain/gateway.py`**: Deleted the `relay_bet()` placeholder method entirely.

## Test Results

**418/419 tests pass.**

**1 failure (p-test-writer action needed):**
- `tests/test_gateway.py::TestBlockchainGateway::test_relay_bet_returns_none`
- **Cause:** Test calls `gateway.relay_bet(...)` but method was deleted as instructed.
- **Fix required:** p-test-writer must remove `test_relay_bet_returns_none` from `tests/test_gateway.py`.

All other 418 tests pass cleanly.

## Handoff

- **Attempted**: All four tasks as specified
- **Worked**: AI Bettor tracking, Moltbook join route, X402 field name fix, .env.example creation, CLAUDE.md cleanup, relay_bet() deletion
- **Failed**: None (all changes implemented correctly)
- **Remaining**: p-test-writer must delete `test_relay_bet_returns_none` in `tests/test_gateway.py` since `relay_bet()` was removed from gateway per task instructions
