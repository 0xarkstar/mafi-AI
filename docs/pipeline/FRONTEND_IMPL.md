# Frontend Implementation Report

## Summary

All frontend changes for the mafia-ai game flow redesign have been implemented and the build passes with 0 errors.

## Changes Made

### 1. `frontend/src/mappers.ts`
- Updated `buildPlayerFromName` signature to accept optional `avatarIndex?: number | null` parameter
- AI agents: uses `avatarIndex ?? index % 8` (backend-provided index takes precedence)
- Human fallback: uses `avatarIndex ?? undefined` (no default for unknown humans)

### 2. `frontend/src/store.ts`
**Removed:**
- `walletConnected: boolean` from interface and initial state
- `walletAddress: string | null` from interface and initial state
- `balance: number` from interface and initial state (was chip balance)
- `connectWallet: () => Promise<void>` entire action removed

**Added:**
- `playAgain: () => void` action — keeps WS alive, sends `rejoin_lobby`, resets game state to LOBBY
- `new_lobby` WS event handler — posts system message when server notifies of new lobby

**Modified:**
- `connectAndJoin` — now sends `avatar_index` in the `join_lobby` WS message
- `lobby_status` handler — supports both structured (`{name, player_type, avatar_index}`) and flat (string) player formats
- `placeBet` — removed `balance: state.balance - amount` mutation (balance field removed)
- `resetGame` — removed `balance: 1000` reset (field removed)

### 3. `frontend/src/screens/LandingScreen.tsx`
**Removed:**
- Wallet connection step (entire two-step flow removed)
- `step` state variable (`'nickname' | 'avatar'`)
- `Wallet`, `ChevronLeft` imports
- `walletConnected`, `walletAddress`, `connectWallet` store references

**New design:** Single-step onboarding
- Nickname input + 4×2 avatar grid shown together on first load
- Default avatar = 0 (first avatar pre-selected, no null state)
- "Join Game" button enabled as soon as nickname is non-empty
- "Spectate Match" secondary button preserved
- All visual effects preserved: shattered mask, floating pieces, mobile fallback, title/branding

### 4. `frontend/src/screens/GameOverScreen.tsx`
**Already modified (by linter/prior tool):**
- `balance` removed from destructuring
- `playAgain` added to destructuring
- Stats grid reduced to single centered "Bets Placed" card (balance card removed)
- "Play Again" → `playAgain()` (WS-connected rejoin)
- "Back to Home" → `resetGame()` (full disconnect + landing)

## Build Verification

```
✓ tsc -b — 0 TypeScript errors
✓ vite build — built in 1.01s, 0 warnings
```

Output:
- `../static/assets/index-C5Cpc9Fz.js` 293.01 kB (86.36 kB gzip)
- `../static/assets/framer-motion-DeQ-TTNY.js` 123.15 kB
- `../static/assets/ethers-l0sNRNKZ.js` 0.00 kB (lazy-loaded, unused now)

## Handoff

- **Attempted**: Incremental edits to each file; full rewrite of LandingScreen
- **Worked**: All 4 files modified successfully, build passes cleanly
- **Failed**: Nothing — all changes applied without issue
- **Remaining**: None for frontend scope. Backend's `rejoin_lobby` handler should be implemented to handle the new WS message from `playAgain()`. The `new_lobby` broadcast from the backend should trigger the `new_lobby` WS event consumed by the store.
