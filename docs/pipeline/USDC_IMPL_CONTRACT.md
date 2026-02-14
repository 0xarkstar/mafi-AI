# USDC Contract Implementation — Handoff

## Summary

Successfully converted MafiaBetting smart contract and frontend from native MON to USDC ERC-20 token on Monad testnet. All 39 tests passing.

## Files Modified

### Smart Contracts
| File | Status | Changes |
|------|--------|---------|
| `contracts/MafiaBetting.sol` | ✅ REWRITTEN | IERC20 USDC, SafeERC20, approve+transferFrom pattern, constructor takes USDC address |
| `contracts/MockERC20.sol` | ✅ CREATED | Simple ERC20 mock with 6 decimals for testing |

### Tests
| File | Status | Changes |
|------|--------|---------|
| `test/MafiaBetting.test.js` | ✅ REWRITTEN | All 39 tests converted to USDC ERC-20 pattern with approve flow |

### Frontend
| File | Status | Changes |
|------|--------|---------|
| `static/blockchain.js` | ✅ MODIFIED | USDC contract initialization, approve+placeBet flow, 6 decimals, balance display |

### Deployment
| File | Status | Changes |
|------|--------|---------|
| `scripts/deploy.js` | ✅ MODIFIED | Deploy with Monad testnet USDC address (0x534b2f3A...) |
| `hardhat.config.js` | ✅ MODIFIED | Fixed private key validation to prevent empty key errors |

### Python Backend
| File | Status | Changes |
|------|--------|---------|
| `src/blockchain/contract.py` | ✅ NO CHANGE | Oracle functions (createGame, settle) work with new ABI |
| `src/blockchain/provider.py` | ✅ NO CHANGE | ABI loaded from artifacts/contracts/MafiaBetting.sol/MafiaBetting.json |

## Key Implementation Details

### 1. Smart Contract (MafiaBetting.sol)

**BEFORE (Native MON):**
```solidity
function placeBet(uint256 gameId, bool betMafia) external payable {
    require(msg.value > 0, ...);
    // Uses msg.value
}

function claimWinnings(uint256 gameId) external {
    ...
    (bool success, ) = msg.sender.call{value: payout}("");
}
```

**AFTER (USDC ERC-20):**
```solidity
IERC20 public immutable usdc;

constructor(address _usdc) Ownable(msg.sender) {
    require(_usdc != address(0), "Invalid USDC address");
    usdc = IERC20(_usdc);
}

function placeBet(uint256 gameId, bool betMafia, uint256 amount) external {
    require(amount > 0, ...);
    usdc.safeTransferFrom(msg.sender, address(this), amount);
    ...
}

function claimWinnings(uint256 gameId) external {
    ...
    usdc.safeTransfer(msg.sender, payout);
}
```

### 2. Tests (MafiaBetting.test.js)

**Pattern:**
1. Deploy MockERC20 with 6 decimals
2. Deploy MafiaBetting with USDC address
3. Mint USDC to test accounts
4. Approve USDC before each bet
5. Use `parseUnits(amount, 6)` for USDC amounts
6. Verify USDC transfers and balances

**Test Count:** 39 tests (5 new USDC-specific tests added)
- ✅ Should set the correct USDC address
- ✅ Should reject zero address for USDC
- ✅ Should not allow betting without USDC approval
- ✅ Should not allow betting with insufficient USDC balance
- ✅ Should transfer USDC from bettor to contract

### 3. Frontend (blockchain.js)

**Flow:**
1. Initialize USDC contract on wallet connect
2. Show USDC balance (6 decimals) instead of MON balance
3. Before placing bet:
   - Check allowance
   - Approve if needed (use MaxUint256 for unlimited approval)
4. Call `contract.placeBet(gameId, betMafia, amount)` with amount parameter
5. Claim winnings transfers USDC back to user

**Decimals:** All amounts use 6 decimals (USDC) instead of 18 (MON)

### 4. Deployment

**Monad Testnet USDC:** `0x534b2f3A21130d7a60830c2Df862319e593943A3`

Deploy command:
```bash
npx hardhat run scripts/deploy.js --network monadTestnet
```

Contract constructor automatically receives USDC address.

## Test Results

```bash
npx hardhat test
```

**Output:**
```
MafiaBetting
  Deployment
    ✔ Should set the correct owner
    ✔ Should have correct fee constants
    ✔ Should set the correct USDC address
    ✔ Should reject zero address for USDC
  Game Creation
    ✔ Should allow owner to create a game
    ✔ Should not allow non-owner to create a game
    ✔ Should not allow creating duplicate games
  Placing Bets
    ✔ Should allow betting on mafia with USDC
    ✔ Should allow betting on citizens with USDC
    ✔ Should allow multiple bets from same player
    ✔ Should not allow zero-value bets
    ✔ Should not allow betting without USDC approval
    ✔ Should not allow betting with insufficient USDC balance
    ✔ Should not allow betting on non-existent game
    ✔ Should not allow betting on locked game
    ✔ Should transfer USDC from bettor to contract
  Locking Betting
    ✔ Should allow owner to lock betting
    ✔ Should not allow non-owner to lock betting
    ✔ Should not allow locking twice
    ✔ Should not allow locking non-existent game
  Settling Games
    ✔ Should allow owner to settle game
    ✔ Should not allow non-owner to settle
    ✔ Should not allow settling unlocked game
    ✔ Should not allow settling twice
    ✔ Should collect house fees on settlement
  Payout Calculation
    ✔ Should calculate correct payout for winner with 5% house edge
    ✔ Should calculate proportional payouts for multiple winners
    ✔ Should return 0 for non-bettors
    ✔ Should return 0 for losers
    ✔ Should return 0 before game is settled
  Claiming Winnings
    ✔ Should allow winner to claim USDC winnings
    ✔ Should not allow claiming twice
    ✔ Should not allow claiming before settlement
    ✔ Should not allow losers to claim
    ✔ Should not allow non-bettors to claim
  Fee Withdrawal
    ✔ Should allow owner to withdraw USDC fees
    ✔ Should not allow non-owner to withdraw fees
    ✔ Should not allow withdrawing with no fees
  Complete Game Lifecycle
    ✔ Should handle complete game flow with multiple bettors using USDC

39 passing (560ms)
```

## Compilation

```bash
npx hardhat compile
```

**Output:**
```
Compiled 11 Solidity files successfully (evm target: paris).
```

**Artifacts generated:**
- `artifacts/contracts/MafiaBetting.sol/MafiaBetting.json` (with updated ABI)
- `artifacts/contracts/MockERC20.sol/MockERC20.json`

## Integration Points

### Python Backend
- `src/blockchain/contract.py` — NO CHANGES NEEDED (oracle functions unchanged)
- `src/blockchain/provider.py` — NO CHANGES NEEDED (loads ABI from artifacts)
- ABI automatically updated after compilation

### Frontend Integration
- MetaMask users must **approve USDC** before placing bets
- UI shows "💵 X.XX USDC" instead of "💎 X.XXXX MON"
- Error handling for insufficient USDC and missing approval

## Dependencies

**OpenZeppelin:**
- `@openzeppelin/contracts/token/ERC20/IERC20.sol`
- `@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol`
- `@openzeppelin/contracts/utils/ReentrancyGuard.sol`
- `@openzeppelin/contracts/access/Ownable.sol`

Already installed via `@openzeppelin/contracts` package.

## Security Features

✅ **SafeERC20:** All token transfers use `safeTransferFrom` and `safeTransfer`
✅ **ReentrancyGuard:** Protected against reentrancy attacks
✅ **Checks-Effects-Interactions:** State updates before external calls
✅ **Access Control:** Ownable for oracle functions
✅ **Input Validation:** Amount > 0, game existence, lock state

## Handoff

### Attempted
- Convert MafiaBetting.sol from native MON to USDC ERC-20
- Create MockERC20 for testing
- Rewrite all 39 tests to use USDC pattern
- Update blockchain.js frontend for USDC approval flow
- Update deployment script with USDC address
- Verify Python backend compatibility

### Worked
- ✅ All 39 tests passing
- ✅ Contract compiles successfully
- ✅ SafeERC20 implementation secure
- ✅ MockERC20 with 6 decimals works for tests
- ✅ Frontend USDC approval flow implemented
- ✅ Python backend oracle functions compatible with new ABI

### Failed
- ❌ None — all implementation tasks completed successfully

### Remaining
- 🔲 Python backend team needs to implement `src/betting/settlement.py` (USDC transfer logic)
- 🔲 Python backend team needs to update `src/models/betting.py` (remove payment_method, make tx_hash required)
- 🔲 Python backend team needs to update `src/betting/manager.py` (unified USDC betting)
- 🔲 Deploy contract to Monad testnet (requires PRIVATE_KEY with MON tokens)
- 🔲 Update `.env` with deployed contract address
- 🔲 Integration testing with live Monad testnet USDC

## Next Steps (for Backend Team)

1. Review `docs/pipeline/USDC_DESIGN.md` for full architecture
2. Implement `src/betting/settlement.py` (USDCSettlement class)
3. Update BettingManager to use single USDC pool
4. Remove chip betting entirely
5. Update API endpoints to use x402 middleware for all bets
6. Run Python tests with new models

## Notes

- **USDC Decimals:** 6 (not 18 like ETH/MON)
- **Monad Testnet USDC:** `0x534b2f3A21130d7a60830c2Df862319e593943A3`
- **Approval Pattern:** Frontend uses `MaxUint256` for unlimited approval (standard practice)
- **Gas Costs:** Similar to before (ERC-20 transfers ~45k gas, approve ~45k gas)
- **Python Backend:** Oracle functions (createGame, settle) work identically with new ABI

## Contact

For questions or issues:
- Contract: `contracts/MafiaBetting.sol` (lines 1-222)
- Tests: `test/MafiaBetting.test.js` (lines 1-423)
- Frontend: `static/blockchain.js` (lines 1-472)
