# USDC Betting Unification — Backend Implementation

## Summary

Successfully implemented all Python backend changes to unify the betting system around USDC with X402 payment protocol. Chip-based betting has been completely removed, and all bets now require X402 USDC payment.

## Files Created

### 1. `src/moltbook/auth.py` (NEW)
**Purpose**: Moltbook Identity token verification

**Key Features**:
- `MoltbookAuth` class with `verify_identity()` method
- POST to `https://moltbook.com/api/v1/agents/verify-identity`
- Headers: `X-Moltbook-App-Key`
- Body: `{"token": identity_token, "audience": audience}`
- Returns: `{"valid": true, "agent": {"id", "name", "wallet_address"}}`
- Error handling: 401 on failure (identity_token_expired, invalid_token, agent_not_found, audience_mismatch)
- 503 on Moltbook service unavailable

### 2. `src/betting/settlement.py` (NEW)
**Purpose**: USDC payout transfers via web3.py

**Key Features**:
- `USDCSettlement` class with `settle_payouts()` and `get_balance()` methods
- Minimal ERC-20 ABI (transfer, balanceOf)
- AsyncWeb3 integration
- USDC has 6 decimals: `amount_raw = int(amount * 10**6)`
- Transfers USDC to each winner's wallet address
- Returns list of `{address, amount, tx_hash}` for each successful transfer
- Comprehensive error handling and logging

## Files Modified

### 3. `src/config/settings.py`
**Changes**:
- ✅ REMOVED: `starting_chips: int = 1000`
- ✅ ADDED: `moltbook_app_key: SecretStr = SecretStr("")`
- ✅ ADDED: `moltbook_audience: str = "mafia-ai.example.com"`
- ✅ ADDED: `settlement_enabled: bool = False`
- ✅ ADDED: `settlement_private_key: SecretStr = SecretStr("")`

### 4. `src/config/constants.py`
**Changes**:
- ✅ ADDED: `from decimal import Decimal` import
- ✅ REMOVED: `DEFAULT_STARTING_CHIPS = 1000`
- ✅ ADDED: `MIN_BET_USDC = Decimal("1.0")`
- ✅ ADDED: `MAX_BET_USDC = Decimal("100.0")`

### 5. `src/models/betting.py`
**Changes**:
- ✅ Bet model: REMOVED `payment_method: str = "chips"`
- ✅ Bet model: changed `tx_hash: str | None = None` to `tx_hash: str` (required)
- ✅ Updated docstring: "wallet address (0x...)" instead of "session id or wallet address"

### 6. `src/betting/manager.py` (MAJOR REWRITE)
**Changes**:
- ✅ REMOVED: `self.spectators: dict[str, Decimal] = {}`
- ✅ REMOVED: `register_spectator()` method
- ✅ REMOVED: `get_spectator_balance()` method
- ✅ REMOVED: Old `place_bet()` method (chip-based)
- ✅ REMOVED: `handle_x402_bet()` method
- ✅ MERGED: Single `place_bet()` method accepting USDC + tx_hash:
  ```python
  def place_bet(self, bettor_address: str, bet_type: str, target: str,
                amount_usdc: Decimal, round_number: int, tx_hash: str) -> Bet | None
  ```
- ✅ ADDED: Amount validation with MIN_BET_USDC, MAX_BET_USDC
- ✅ MODIFIED: `settle()` returns `dict[str, Decimal]` (wallet_address → payout_usdc)
- ✅ MODIFIED: `settle_identity_bets()` returns `dict[str, Decimal]` (wallet_address → payout_usdc)
- ✅ REMOVED: All spectator balance mutations

### 7. `src/x402/middleware.py`
**Changes**:
- ✅ MODIFIED: `protected_paths` changed from `["/api/bets/x402"]` to `["/api/bets"]`
- ✅ MODIFIED: `register()` route_pattern changed from `"/api/bets/x402"` to `"/api/bets"`
- ✅ MODIFIED: When x402_enabled=False, protected paths return 503 Service Unavailable
- ✅ REMOVED: Test mode fallback (lines 104-107 with X-Test-Address header)

### 8. `src/api/server.py`
**Changes**:
- ✅ RENAMED: `/api/bets/x402` → `/api/bets` (unified endpoint)
- ✅ REMOVED: Test mode chip fallback (x402_enabled=False branch)
- ✅ MODIFIED: Always requires `request.state.x402_payment` (injected by middleware)
- ✅ MODIFIED: Calls `place_bet()` instead of `handle_x402_bet()`
- ✅ MODIFIED: `/api/lobby/join-agent` endpoint:
  - Now reads `X-Moltbook-Identity` header
  - Calls `MoltbookAuth.verify_identity(token)`
  - Extracts verified agent info (id, name, wallet_address)
  - Creates `MoltbookAgentPlayer` with verified identity
  - Returns wallet_address in response
- ✅ MODIFIED: WebSocket `place_bet` handler:
  - Now sends `bet_info` message directing to REST API
  - Message: "Betting is via REST API only"
  - Endpoint: "POST /api/bets"
  - Instructions: "Use X402 payment protocol to place bets"

### 9. `src/engine/game_engine.py`
**Changes**:
- ✅ REMOVED: Blockchain contract settlement in side_win settlement block
- ✅ MODIFIED: `settle()` only calculates payouts, doesn't modify balances
- ✅ ADDED: Combined payouts from side_win + identity bets
- ✅ ADDED: USDC settlement integration (optional via `settlement_enabled`):
  - Imports `USDCSettlement` and `create_web3_provider`
  - Initializes AsyncWeb3 with Monad testnet RPC
  - Creates USDCSettlement instance
  - Calls `settle_payouts(combined_payouts)`
  - Broadcasts `usdc_settlement` event with transfer results
  - Comprehensive error handling

### 10. `src/ai_bettor/client.py`
**Changes**:
- ✅ MODIFIED: `_place_bet_via_api()` method:
  - Changed URL from `/api/bets/x402` to `/api/bets`
  - Added TODO comment for X402 payment signing
  - Note: Will fail with 402 Payment Required until X402 signing is implemented

### 11. `src/moltbook/__init__.py`
**Changes**:
- ✅ ADDED: Import and export `MoltbookAuth`
- ✅ Updated `__all__ = ["MoltbookAuth", "MoltbookClient"]`

## Import Verification

All imports verified working:
- ✅ `from src.moltbook.auth import MoltbookAuth`
- ✅ `from src.config.settings import Settings`
- ✅ `from src.config.constants import MIN_BET_USDC, MAX_BET_USDC`
- ✅ `from src.models.betting import Bet`
- ✅ `from src.betting.manager import BettingManager`
- ✅ `from src.betting.settlement import USDCSettlement`

## Key Architectural Changes

1. **Single Currency**: USDC is now the only betting currency
2. **No Chip Balances**: Removed `spectators` dict entirely
3. **Unified Betting**: Single `place_bet()` method replacing chip-based and x402 methods
4. **Moltbook Identity**: Proper JWT-based authentication replacing API key stub
5. **USDC Settlement**: Server-side web3 transfers to winners (optional)
6. **X402 Required**: All bets require x402 payment (no test mode fallback)

## Migration Guide

### Before (Chip-based)
```python
# Register spectator
betting_manager.register_spectator(session_id)

# Place chip bet
bet = betting_manager.place_bet(session_id, "side_win", "citizens", 100, 0)

# Check balance
balance = betting_manager.get_spectator_balance(session_id)

# Settle (adds to chip balances)
payouts = betting_manager.settle("citizens")
```

### After (USDC-based)
```python
# No registration needed

# Place USDC bet (via X402 payment)
bet = betting_manager.place_bet(
    bettor_address="0x742d...",
    bet_type="side_win",
    target="citizens",
    amount_usdc=Decimal("5.0"),
    round_number=0,
    tx_hash="0xabcd..."
)

# No balance checking (payment already verified by X402)

# Settle (returns wallet_address → payout_usdc dict)
payouts = betting_manager.settle("citizens")

# Optional: Transfer USDC to winners
if settlement_enabled:
    settlement = USDCSettlement(w3, usdc_address, private_key)
    results = await settlement.settle_payouts(payouts)
```

## Testing Impact

The following test files will need updates:
- `tests/test_betting.py` — All tests to use USDC instead of chips
- `tests/test_x402.py` — Update endpoint from /x402 to /bets
- `tests/test_x402_betting.py` — Integration tests for unified endpoint
- `tests/test_api.py` — WebSocket place_bet handler, join-agent endpoint
- `tests/test_ai_bettor.py` — X402 payment integration (TODO)
- NEW: `tests/test_moltbook_auth.py` — Moltbook Identity verification
- NEW: `tests/test_settlement.py` — USDC settlement tests

## Known Issues

1. **AI Bettor X402 Signing**: `src/ai_bettor/client.py` has TODO for X402 payment signing
   - Currently will fail with 402 Payment Required
   - Needs x-payment header with signed EIP-712 TypedData

2. **Settlement Private Key**: `settlement_enabled` requires `settlement_private_key` in .env
   - Server wallet must have MON tokens for gas
   - Server wallet must have USDC balance to pay out winners

3. **Moltbook App Key**: Requires `moltbook_app_key` in .env for agent authentication
   - Format: `moltdev_xxx` (development) or `moltprod_xxx` (production)

## Environment Variables Required

```bash
# Moltbook Identity
MOLTBOOK_APP_KEY=moltdev_your_app_key_here
MOLTBOOK_AUDIENCE=mafia-ai.example.com

# USDC Settlement (optional)
SETTLEMENT_ENABLED=true
SETTLEMENT_PRIVATE_KEY=0xyour_server_wallet_private_key

# X402 (required for betting)
X402_ENABLED=true
X402_FACILITATOR_URL=https://x402-facilitator.molandak.org
X402_NETWORK=eip155:10143
X402_USDC_ADDRESS=0x534b2f3A21130d7a60830c2Df862319e593943A3
X402_PAY_TO=0xyour_server_wallet_address
```

## Handoff

### Attempted
All 10 backend files from the USDC_DESIGN.md file ownership map:
1. Created `src/moltbook/auth.py` with MoltbookAuth class
2. Modified `src/config/settings.py` with new fields
3. Modified `src/config/constants.py` with USDC limits
4. Modified `src/models/betting.py` Bet model
5. Major rewrite of `src/betting/manager.py` (removed spectators, unified place_bet)
6. Created `src/betting/settlement.py` with USDCSettlement class
7. Modified `src/x402/middleware.py` (removed test mode)
8. Modified `src/api/server.py` (Moltbook Identity, unified /api/bets, WebSocket redirect)
9. Modified `src/engine/game_engine.py` (USDC settlement integration)
10. Modified `src/ai_bettor/client.py` (unified endpoint with TODO)

### Worked
- All 10 files successfully created/modified
- All imports verified working (no import errors)
- Immutability preserved (all Pydantic models remain frozen=True)
- Consistent logging with structlog
- Error handling comprehensive (HTTPException, try/except blocks)
- Code style follows existing patterns (read files before modifying)

### Failed
None. All planned changes completed successfully.

### Remaining
1. **Tests Need Updates**: All betting-related tests need to be updated for USDC-based system
   - Remove chip balance checks
   - Use wallet addresses instead of session IDs
   - Mock X402 payment info in request.state
   - Test Moltbook Identity verification
   - Test USDC settlement transfers

2. **AI Bettor X402 Integration**: `_place_bet_via_api()` needs X402 payment signing
   - Import X402 SDK
   - Sign EIP-712 TypedData for payment
   - Add x-payment header to POST /api/bets request

3. **Smart Contract Changes**: p-impl-contract needs to update:
   - `contracts/MafiaBetting.sol` to use IERC20 USDC
   - `src/blockchain/contract.py` to match new contract
   - `static/blockchain.js` for USDC approve() pattern
   - All Hardhat tests to use mock USDC

4. **Integration Testing**: End-to-end flow with real X402 facilitator
   - Test X402 payment on Monad testnet
   - Verify USDC transfers to winners
   - Test Moltbook Identity token verification

5. **Documentation**: Update CLAUDE.md with new betting flow
   - Remove references to chips
   - Document X402 payment requirement
   - Add Moltbook Identity authentication guide
