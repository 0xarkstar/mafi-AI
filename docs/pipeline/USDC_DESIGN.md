# USDC Betting Unification — Design Document

## Problem Statement

MafiaAI currently has **3 fragmented betting systems** that don't integrate:

1. **Chips** (in-memory) — `place_bet()` in BettingManager, deducts from `spectators` dict
2. **MON** (on-chain) — `MafiaBetting.sol` uses `msg.value` native MON, completely separate pool
3. **USDC** (x402) — `handle_x402_bet()` accepts USDC payment but records bet as chips internally

**Critical bugs:**
- USDC paid via x402 → bet recorded → settlement adds to chip balance (money evaporates)
- MON pool on-chain is entirely separate from server-side chip pool
- Odds calculation only reflects chip pool, ignoring MON/USDC bets
- No unified view of total betting activity

## Solution: Single USDC Currency

**One currency. One pool. One settlement path.**

- **USDC** is the sole betting currency (MON used only for gas)
- All bets go through **x402 protocol** (HTTP 402 Payment Required)
- Single **pari-mutuel pool** with 5% house edge
- Server-side **USDC settlement** via web3.py transfers
- **Remove chips entirely** — no more `spectators` dict, no `DEFAULT_STARTING_CHIPS`

## Architecture

### Authentication: Sign in with Moltbook

**New file: `src/moltbook/auth.py`**

Moltbook agents authenticate via identity tokens:

```
Agent → POST /agents/me/identity-token (Bearer API_KEY) → gets JWT
Agent → POST /api/lobby/join-agent with X-Moltbook-Identity header
Server → POST https://moltbook.com/api/v1/agents/verify-identity
         Headers: X-Moltbook-App-Key: moltdev_xxx
         Body: {"token": identity_token, "audience": "mafia-ai.example.com"}
Server ← {"valid": true, "agent": {"id": "...", "name": "...", "wallet_address": "0x..."}}
```

Key details:
- Tokens expire in **1 hour** (signed JWTs)
- `audience` restriction prevents token forwarding between apps
- Error codes: `identity_token_expired`, `invalid_token`, `agent_not_found`, `audience_mismatch`
- Rate limit: **100 req/min** per app
- Verification endpoint: `https://moltbook.com/api/v1/agents/verify-identity`

### Payment: x402 Protocol

All bets require x402 USDC payment:

```
Bettor → POST /api/bets (no x-payment header)
Server ← 402 Payment Required (with payment requirements JSON)
Bettor → Signs EIP-712 TypedData via wallet
Bettor → POST /api/bets (with x-payment header containing signed payment)
Server → Forwards to facilitator for verification
Facilitator → Verifies signature + settles USDC to server wallet
Server ← Payment verified (payer_address, amount_usdc, tx_hash)
Server → Places bet in pool
```

Monad testnet details:
- Chain ID: **10143**
- USDC address: `0x534b2f3A21130d7a60830c2Df862319e593943A3`
- Facilitator: `https://x402-facilitator.molandak.org`
- Facilitator pays gas (bettor pays nothing except USDC)

### Betting: Unified Pari-mutuel Pool

Single BettingManager pool (USDC only):

```python
class BettingManager:
    def __init__(self, llm_client, game_id):
        self.pools: dict[BetType, BettingPool] = {...}
        # NO spectators dict
        # NO chip balances

    def place_bet(self, bettor_address, bet_type, target, amount_usdc,
                  round_number, tx_hash) -> Bet | None:
        """Single unified bet placement. All bets are USDC with tx_hash."""
        ...

    def settle(self, winner) -> dict[str, Decimal]:
        """Returns {wallet_address: payout_usdc} for USDC transfer."""
        ...
```

### Settlement: Server-side USDC Transfer

**New file: `src/betting/settlement.py`**

After game ends, server transfers USDC to winners:

```python
class USDCSettlement:
    def __init__(self, web3_provider, usdc_address, server_private_key):
        self.w3 = web3_provider
        self.usdc = self.w3.eth.contract(address=usdc_address, abi=ERC20_ABI)

    async def settle_payouts(self, payouts: dict[str, Decimal]) -> list[str]:
        """Transfer USDC to each winner. Returns list of tx hashes."""
        for address, amount in payouts.items():
            amount_raw = int(amount * Decimal("1000000"))  # 6 decimals
            tx = self.usdc.functions.transfer(address, amount_raw)
            ...
```

### Smart Contract: USDC ERC-20

**Rewrite: `contracts/MafiaBetting.sol`**

Convert from native MON (`msg.value`) to USDC ERC-20 (`transferFrom/transfer`):

```solidity
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MafiaBetting is ReentrancyGuard, Ownable {
    IERC20 public immutable usdc;

    constructor(address _usdc) Ownable(msg.sender) {
        usdc = IERC20(_usdc);
    }

    function placeBet(uint256 gameId, bool betMafia, uint256 amount) external {
        // User must approve() first
        usdc.transferFrom(msg.sender, address(this), amount);
        ...
    }

    function claimWinnings(uint256 gameId) external {
        ...
        usdc.transfer(msg.sender, payout);
    }
}
```

## File Ownership Map

### p-impl-backend (sonnet) — Python backend changes
| File | Action |
|------|--------|
| `src/moltbook/auth.py` | **CREATE** — MoltbookAuth class with verify_identity() |
| `src/config/settings.py` | **MODIFY** — add moltbook_app_key, moltbook_audience; remove starting_chips |
| `src/config/constants.py` | **MODIFY** — remove DEFAULT_STARTING_CHIPS; add MIN_BET_USDC, MAX_BET_USDC |
| `src/models/betting.py` | **MODIFY** — Bet: remove payment_method, add bettor_address, make tx_hash required |
| `src/betting/manager.py` | **MODIFY** — MAJOR REWRITE: remove spectators dict, remove place_bet(chips), merge handle_x402_bet into single place_bet(USDC), settle returns addresses+amounts |
| `src/betting/settlement.py` | **CREATE** — USDCSettlement class for web3 USDC transfers |
| `src/x402/middleware.py` | **MODIFY** — simplify: remove test mode chip fallback |
| `src/api/server.py` | **MODIFY** — join-agent endpoint: use Moltbook Identity; merge /api/bets/x402 into /api/bets; WebSocket place_bet: proxy through x402 |
| `src/engine/game_engine.py` | **MODIFY** — settle() calls USDCSettlement instead of chip credits |
| `src/ai_bettor/client.py` | **MODIFY** — use x402 payment for bets |
| `tests/` | **MODIFY** — update all betting/x402/api/auth tests |

### p-impl-contract (sonnet) — Smart contract + frontend
| File | Action |
|------|--------|
| `contracts/MafiaBetting.sol` | **MODIFY** — MAJOR REWRITE: IERC20 USDC, approve+transferFrom pattern |
| `src/blockchain/contract.py` | **MODIFY** — update create_game, settle to match new contract |
| `src/blockchain/provider.py` | **MODIFY** — ensure USDC contract loading |
| `static/blockchain.js` | **MODIFY** — USDC approve() → placeBet(amount), remove msg.value |
| `test/MafiaBetting.test.js` | **MODIFY** — all tests use mock USDC ERC-20 |
| `scripts/deploy.js` | **MODIFY** — deploy with USDC address parameter |

### p-test-writer (sonnet) — Test suite
| File | Action |
|------|--------|
| `tests/test_moltbook_auth.py` | **CREATE** — Moltbook Identity auth tests |
| `tests/test_betting.py` | **MODIFY** — all USDC-based, no chips |
| `tests/test_x402.py` | **MODIFY** — unified endpoint tests |
| `tests/test_x402_betting.py` | **MODIFY** — x402+betting integration |
| `tests/test_api.py` | **MODIFY** — new auth flow, unified bet endpoint |
| `tests/test_ai_bettor.py` | **MODIFY** — x402 payment integration |
| `tests/test_settlement.py` | **CREATE** — USDCSettlement tests |

## Key Decisions

1. **USDC over MON** — Hackathon provides 6 Circle/USDC resources, x402 is USDC-only, stablecoin better for wagering
2. **Server-side settlement** — Server wallet holds USDC, transfers to winners via web3.py after game ends
3. **No chips** — Remove entirely, not even as fallback. Clean break.
4. **x402 for ALL bets** — WebSocket spectators, REST agents, AI Bettor — all use x402
5. **Moltbook Identity** — Proper JWT-based auth replacing the TODO stub
6. **Smart contract dual path** — Keep on-chain option (users interact directly via MetaMask) alongside server-side pool
7. **ERC-20 pattern** — `approve() → transferFrom()` for contract, direct `transfer()` for server settlement

## Models After Changes

### Bet (modified)
```python
class Bet(BaseModel, frozen=True):
    bet_id: str
    game_id: str
    bettor_id: str           # wallet address (0x...)
    bet_type: BetType
    target: str
    amount: Decimal           # USDC amount
    round_placed: int
    weight: Decimal = Decimal("1.0")
    tx_hash: str              # REQUIRED — always has x402 tx hash
    # REMOVED: payment_method
```

### Settings (modified)
```python
class Settings(BaseSettings):
    # ... existing fields ...
    # REMOVE: starting_chips

    # ADD: Moltbook Identity
    moltbook_app_key: SecretStr = SecretStr("")      # moltdev_xxx
    moltbook_audience: str = "mafia-ai.example.com"  # audience restriction

    # ADD: USDC Settlement
    settlement_enabled: bool = False
    settlement_private_key: SecretStr = SecretStr("")  # server wallet for USDC transfers
```

### Constants (modified)
```python
# REMOVE: DEFAULT_STARTING_CHIPS = 1000
# ADD:
MIN_BET_USDC = Decimal("1.0")    # $1 minimum
MAX_BET_USDC = Decimal("100.0")  # $100 maximum
```

## Handoff

- **Attempted**: Full analysis of 3-way betting fragmentation, Moltbook API research, x402 protocol research, hackathon resource analysis
- **Worked**: Architecture finalized, all decisions made, file ownership map complete
- **Failed**: N/A (design phase)
- **Remaining**: Implementation of all changes per file ownership map
