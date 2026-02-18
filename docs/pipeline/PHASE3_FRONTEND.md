# Phase 3 Frontend Fixes

**Agent**: p-impl-frontend
**Date**: 2026-02-18
**Build status**: ✅ `npm run build` — 0 errors, 0 warnings

---

## Summary

Fixed all 3 CRITICAL memory leaks and store timeout management issues. The build passes cleanly.

---

## CRITICAL Memory Leaks Fixed (3)

### 1. SpectatorScreen.tsx — `setActiveSpeakerId(null)` timeout leak

**File**: `frontend/src/screens/SpectatorScreen.tsx`

Added `activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)`.

- Before each `setTimeout(() => setActiveSpeakerId(null), 3000)`, clears any previous pending timer via the ref.
- Stores new timer ID in the ref.
- Cleanup useEffect clears timer on unmount.

**Pattern**:
```typescript
const activeSpeakerTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
// In effect:
if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current);
activeSpeakerTimerRef.current = setTimeout(() => setActiveSpeakerId(null), 3000);
// Cleanup useEffect:
useEffect(() => () => { if (activeSpeakerTimerRef.current) clearTimeout(activeSpeakerTimerRef.current); }, []);
```

### 2. SpectatorScreen.tsx — `setBetSuccess(false)` timeout leak

**File**: `frontend/src/screens/SpectatorScreen.tsx`

Added `betSuccessTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)`.

- `handlePlaceBet` is a regular event handler; the 2s `setBetSuccess(false)` timer could fire after unmount.
- Stores timer ID in ref; cleared on unmount in the same cleanup useEffect.

### 3. GameScreen.tsx — `setActiveSpeakerId(null)` timeout leak

**File**: `frontend/src/screens/GameScreen.tsx`

Same pattern as fix #1 applied to `GameScreen.tsx`.

Added `activeSpeakerTimerRef` ref, clears previous timer before creating new one, cleanup useEffect on unmount.

**Note**: The night overlay timer (`setShowNightOverlay(false)`) and countdown timer in `GameScreen.tsx` were already properly cleaned up via `return () => clearTimeout(timer)` inside their useEffects — no change needed there.

---

## Store Timeout Cleanup Fixed (2)

### 4. store.ts — `game_over` handler 15s timeout

**File**: `frontend/src/store.ts`

Added module-level variable `let gameOverTimeoutId: ReturnType<typeof setTimeout> | null = null;`.

- `game_over` handler clears any existing timeout before setting a new one.
- `resetGame()` clears and nulls `gameOverTimeoutId`.
- `playAgain()` clears and nulls `gameOverTimeoutId`.

### 5. store.ts — `triggerEmote` 3s timeout

**File**: `frontend/src/store.ts`

Added module-level `const emoteTimeoutIds = new Map<string, ReturnType<typeof setTimeout>>();`.

- Tracks one timeout per playerId; cancels existing before setting new one.
- `resetGame()` clears all emote timeouts via `emoteTimeoutIds.forEach(clearTimeout)` then `emoteTimeoutIds.clear()`.

---

## HIGH Issues Assessment

The REVIEW_FRONTEND.md was written against an expected architecture (with `hooks/useWebSocket.ts`, `hooks/useBetting.ts`, `components/game/ActionPanel.tsx`) that differs from the actual codebase. Mapping to actual files:

- **Issue 6** (ActionPanel stale closure): `ActionPanel.tsx` does not exist as a separate file. The vote handler in `GameScreen.tsx` reads from Zustand directly — no stale closure risk.
- **Issue 7** (missing exhaustive-deps): The `setTarget` dependency mentioned in the review does not apply to the actual `SpectatorScreen.tsx` — the state setter pattern used (`setBetTarget`) is a React state setter and stable.
- **Issue 8** (`any` type in WS handlers): `handleWSEvent: (event: any)` in `store.ts` — this is a Zustand store method signature; tightening requires defining typed discriminated union for all 15+ event types. Deferred as scope expansion beyond the leak fixes.
- **Issue 9** (missing useCallback deps): No bare `useCallback` without deps found in the codebase.

---

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/screens/SpectatorScreen.tsx` | Added 2 refs, 2 cleanup-ref patterns, 1 cleanup useEffect |
| `frontend/src/screens/GameScreen.tsx` | Added 1 ref, 1 cleanup-ref pattern, 1 cleanup useEffect |
| `frontend/src/store.ts` | Added 2 module-level timeout trackers, updated game_over/triggerEmote/resetGame/playAgain |

---

## Already-Correct Patterns (Not Changed)

- `SpectatorScreen.tsx` countdown timer — already has `return () => clearTimeout(timerId)` ✅
- `GameScreen.tsx` night overlay timer — already has `return () => clearTimeout(timer)` ✅
- `GameScreen.tsx` countdown timer — already has `return () => clearTimeout(timerId)` ✅
- Spectator chat `setInterval` — already has `return () => clearInterval(interval)` ✅
- Bubble timers (`bubbleTimers` Map) — already cleared before creating new ones ✅

---

## Handoff

### Attempted
- Full read of `REVIEW_FRONTEND.md`, `SpectatorScreen.tsx`, `GameScreen.tsx`, `store.ts`
- Reconciliation of review findings against actual code structure (review was for different architecture)
- Fixed all timeout leaks that actually exist in the code

### Worked
- All 3 CRITICAL memory leaks fixed with `useRef` + `clearTimeout` pattern
- Store module-level timeout tracking added
- `npm run build` passes: 0 TypeScript errors, 0 warnings

### Failed
- HIGH issues 6-9 from the review don't map to the actual codebase (different architecture assumed by reviewer)
- `any` type in `handleWSEvent` not typed — would require defining 15+ discriminated union types, deferred

### Remaining
- Optionally: type `handleWSEvent(event: any)` with a proper `WSEvent` discriminated union
- Optionally: add React.memo to `GamePlayerCard` (MEDIUM performance issue from review)
- Optionally: ARIA labels on icon-only buttons (MEDIUM accessibility issue)
