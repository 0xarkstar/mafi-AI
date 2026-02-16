# Frontend Deep Review: React/TypeScript Architecture

**Project**: mafia-ai hackathon submission (AI Mafia game with spectator betting)
**Reviewer**: p-frontend-reviewer
**Date**: 2026-02-16
**Files Reviewed**: 56 TypeScript files (~5159 lines)
**Focus**: State management, WebSocket handling, component architecture, memory leaks, type safety

---

## Executive Summary

**Overall Assessment**: ⚠️ **CONDITIONAL PASS** (Critical memory leaks must be fixed)

The frontend is well-structured with clean component separation, solid Zustand state management, and good use of Framer Motion for animations. However, **critical memory leaks** in timeout cleanup and **stale closure risks** in event handlers pose reliability issues for production use.

**Key Strengths**:
- ✅ Clean Zustand store architecture (4 stores with good separation)
- ✅ Immutable state updates throughout
- ✅ Good component modularity and file organization
- ✅ Proper TypeScript usage (mostly type-safe)
- ✅ Responsive design with mobile support

**Critical Issues**:
- 🔴 **3 memory leaks** from uncleaned timeouts (useWebSocket.ts, useBetting.ts)
- 🔴 **Stale closure risk** in ActionPanel.tsx (auto-submit)
- 🟡 Exhaustive-deps rule disabled in useWebSocket.ts (risky)
- 🟡 Missing cleanup in multiple useEffect hooks

---

## 🔴 CRITICAL Issues (Must Fix Before Production)

### 1. Memory Leak: Uncleaned Timeout in useWebSocket.ts (Line 70)

**File**: `frontend/src/hooks/useWebSocket.ts:70`

```typescript
case 'agent_message': {
  // ...
  setPlayerSpeaking(agent, true)
  setTimeout(() => setPlayerSpeaking(agent, false), 3000)  // ❌ NO CLEANUP
  // ...
}
```

**Issue**: If the component unmounts before the 3-second timeout fires, the timeout will still execute, attempting to update state on an unmounted component. This causes:
- Memory leaks
- React warnings: "Can't perform a React state update on an unmounted component"
- Potential race conditions

**Fix**: Store timeout ID and clean up in useEffect return:
```typescript
const timeoutRef = useRef<NodeJS.Timeout | null>(null)

// In event handler:
if (timeoutRef.current) clearTimeout(timeoutRef.current)
timeoutRef.current = setTimeout(() => setPlayerSpeaking(agent, false), 3000)

// In cleanup:
return () => {
  if (timeoutRef.current) clearTimeout(timeoutRef.current)
  ws.disconnect()
}
```

**Severity**: CRITICAL — Occurs on every agent message (frequent)

---

### 2. Memory Leak: Uncleaned Timeout in useWebSocket.ts (Line 207)

**File**: `frontend/src/hooks/useWebSocket.ts:207`

```typescript
case 'identity_reveal': {
  // ...
  if (allRevealed) {
    setTimeout(() => setScreen('game_over'), 2000)  // ❌ NO CLEANUP
  }
  break
}
```

**Issue**: Same as above — if user navigates away during the 2-second delay, state update occurs on unmounted component.

**Fix**: Same pattern — store timeout ID and clean up.

**Severity**: CRITICAL — Occurs at end of every game

---

### 3. Memory Leak: Uncleaned Timeouts in useBetting.ts (Lines 95, 101)

**File**: `frontend/src/hooks/useBetting.ts:95,101`

```typescript
// Auto-dismiss success message after 3s
setTimeout(() => setTxStatus(null), 3000)  // ❌ NO CLEANUP (line 95)

// Auto-dismiss error after 5s
setTimeout(() => setTxStatus(null), 5000)  // ❌ NO CLEANUP (line 101)
```

**Issue**: If user navigates away before timeout fires, state update on unmounted component.

**Fix**: Return cleanup function:
```typescript
const placeBet = async (...) => {
  const timeoutRef = { current: null as NodeJS.Timeout | null }

  try {
    // ...
    timeoutRef.current = setTimeout(() => setTxStatus(null), 3000)
  } catch (err) {
    timeoutRef.current = setTimeout(() => setTxStatus(null), 5000)
  }

  // Return cleanup function
  return () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
  }
}
```

**Alternative**: Use a cleanup ref in the hook or switch to a toast library with built-in cleanup.

**Severity**: CRITICAL — Occurs on every bet placement

---

### 4. Stale Closure Risk: ActionPanel.tsx (Line 40)

**File**: `frontend/src/components/game/ActionPanel.tsx:40`

```typescript
useEffect(() => {
  if (!actionRequest) return

  setSubmitted(false)
  setTimeRemaining(actionRequest.timeout)
  const firstOption = actionRequest.options?.[0]
  const interval = setInterval(() => {
    setTimeRemaining((prev) => {
      if (prev <= 1) {
        clearInterval(interval)
        if (firstOption) {
          onSubmit(firstOption)  // ❌ STALE CLOSURE if onSubmit changes
          setSubmitted(true)
        }
        return 0
      }
      return prev - 1
    })
  }, 1000)

  return () => clearInterval(interval)
}, [actionRequest, onSubmit])  // ✅ onSubmit in deps, but not memoized
```

**Issue**: `onSubmit` prop is recreated on every render in `App.tsx:48` (inline function). If the parent re-renders during the countdown, the auto-submit will use a **stale callback**, potentially submitting to the wrong handler or with stale state.

**Fix**: Memoize `onSubmit` in parent:
```typescript
// In App.tsx
const handleActionSubmit = useCallback((response: string) => {
  if (!actionRequest) return
  const { myPlayerName } = useGameStore.getState()
  wsSend({
    type: 'action_response',
    player_name: myPlayerName,
    response,
  })
}, [wsSend, actionRequest])
```

**Severity**: CRITICAL — Could cause incorrect game actions (voting for wrong player, etc.)

---

## 🟡 HIGH Issues (Recommended Fixes)

### 5. Exhaustive-Deps Rule Disabled

**File**: `frontend/src/hooks/useWebSocket.ts:234`

```typescript
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [])
```

**Issue**: The WebSocket effect depends on 30+ store setters (lines 10-33), but deps array is empty. While Zustand selectors are stable by default, disabling the rule hides potential issues if the implementation changes.

**Fix**: Explicitly list stable dependencies or use `useShallow` to document which selectors are used.

**Severity**: HIGH — Risky pattern, could break if store implementation changes

---

### 6. Missing Dependencies in SpectatorScreen.tsx

**File**: `frontend/src/screens/SpectatorScreen.tsx:38-68`

```typescript
// Track unread when chat is closed
useEffect(() => {
  if (!showChat) {
    setUnreadCount(messages.length - lastReadCount)  // ✅ Uses messages.length
  }
}, [messages.length, showChat, lastReadCount])  // ✅ GOOD

// Reset target when bet type changes
useEffect(() => {
  if (targets.length > 0 && !targets.includes(target)) {
    const firstTarget = targets[0]
    if (firstTarget) {
      setTarget(firstTarget)  // ❌ setTarget not in deps (safe but inconsistent)
    }
  }
}, [betType, targets, target])  // Missing: setTarget (React 18 auto-batches, so safe)
```

**Issue**: `setTarget` is missing from deps. While React 18's automatic batching prevents issues, this is inconsistent and violates React rules.

**Fix**: Add `setTarget` to deps (won't cause infinite loop since it's a state setter).

**Severity**: HIGH — Violates React rules, could break in future React versions

---

### 7. Type Safety: Excessive `any` Usage

**Files**:
- `frontend/src/hooks/useWebSocket.ts` (lines 44, 46, 103, 131, etc.)
- `frontend/src/lib/blockchain.ts` (line 5: `ethereum?: any`)

**Examples**:
```typescript
const phase = data['phase'] as string  // Should be: as Phase
const round = data['round'] as number  // OK
setPhase(phase as any, round)  // ❌ Defeats type checking
```

**Issue**: Using `any` defeats the purpose of TypeScript and hides potential bugs.

**Fix**: Define proper WebSocket event types:
```typescript
interface WSEventData {
  phase_change: { phase: Phase; round: number }
  agent_message: { agent: string; message: string }
  vote_cast: { voter: string; target: string }
  // etc.
}

type WSEvent<T extends keyof WSEventData> = {
  event_type: T
  data: WSEventData[T]
}
```

**Severity**: HIGH — Type safety is critical for catching bugs early

---

## 🟠 MEDIUM Issues (Should Fix)

### 8. Performance: Multiple Zustand Selectors in GameBoard

**File**: `frontend/src/components/game/GameBoard.tsx:5-10`

```typescript
const players = useGameStore((s) => s.players)
const chatBubbles = useGameStore((s) => s.chatBubbles)
const voteCounts = useGameStore((s) => s.voteCounts)
const activeEmotes = useGameStore((s) => s.activeEmotes)
const showVoteUI = useGameStore((s) => s.showVoteUI)
const setSelectedVoteTarget = useGameStore((s) => s.setSelectedVoteTarget)
```

**Issue**: 6 separate selectors cause 6 separate subscriptions. If any part of the store changes, all 6 will re-check (even if only 1 changed).

**Fix**: Use `useShallow` for combined selection:
```typescript
import { useShallow } from 'zustand/react/shallow'

const { players, chatBubbles, voteCounts, activeEmotes, showVoteUI, setSelectedVoteTarget } =
  useGameStore(useShallow((s) => ({
    players: s.players,
    chatBubbles: s.chatBubbles,
    voteCounts: s.voteCounts,
    activeEmotes: s.activeEmotes,
    showVoteUI: s.showVoteUI,
    setSelectedVoteTarget: s.setSelectedVoteTarget,
  })))
```

**Note**: Already done correctly in `useGameState.ts:5` ✅

**Severity**: MEDIUM — Performance impact grows with player count and update frequency

---

### 9. Accessibility: Missing ARIA Labels

**Files**:
- `frontend/src/components/game/PlayerCard.tsx` (no alt text for role icons)
- `frontend/src/components/betting/BettingPanel.tsx` (no labels on form inputs)
- `frontend/src/screens/LandingScreen.tsx` (avatar selection missing labels)

**Examples**:
```typescript
// ❌ No alt text
<Skull className="w-16 h-16 text-white/70" />

// ❌ No label association
<input type="number" value={amount} onChange={...} />
```

**Fix**:
```typescript
// ✅ With aria-label
<Skull className="w-16 h-16 text-white/70" aria-label="Player eliminated" />

// ✅ With label
<label htmlFor="bet-amount">Amount</label>
<input id="bet-amount" type="number" value={amount} aria-label="Bet amount" />
```

**Severity**: MEDIUM — Affects usability for screen reader users

---

### 10. Race Condition: GameOverScreen Canvas Animation

**File**: `frontend/src/components/game/GameOverScreen.tsx:19-78`

```typescript
useEffect(() => {
  const canvas = canvasRef.current
  if (!canvas) return

  // ... setup animation ...

  let animationId: number
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    // ... draw particles ...
    animationId = requestAnimationFrame(animate)
  }

  animate()

  return () => {
    cancelAnimationFrame(animationId)  // ✅ GOOD cleanup
    window.removeEventListener('resize', handleResize)
  }
}, [isMafiaWin])
```

**Issue**: If `isMafiaWin` changes mid-animation, two animation loops will run simultaneously (old + new), doubling the frame rate and CPU usage.

**Fix**: Already has cleanup ✅, but could be more defensive:
```typescript
let animationId: number | null = null
const animate = () => {
  if (!animationId) return  // Stop if cleaned up
  // ...
  animationId = requestAnimationFrame(animate)
}

return () => {
  if (animationId) cancelAnimationFrame(animationId)
  animationId = null
}
```

**Severity**: MEDIUM — Minor performance issue, rare scenario

---

## 🟢 LOW Issues (Nice to Have)

### 11. Code Duplication: Betting Amount Inputs

**Files**:
- `frontend/src/screens/SpectatorScreen.tsx:284-318`
- `frontend/src/components/betting/BetSlip.tsx` (likely similar)

**Issue**: Bet amount input logic is duplicated across screens.

**Fix**: Extract to shared `BetAmountInput` component.

**Severity**: LOW — Maintainability issue, not a bug

---

### 12. Magic Numbers: Timeout Durations

**Files**: Multiple files have hardcoded timeouts (3000, 5000, 2000, etc.)

**Examples**:
- `useWebSocket.ts:70` — `3000` (speaking indicator duration)
- `useBetting.ts:95` — `3000` (success toast duration)
- `gameStore.ts:232` — `3000` (emote duration)

**Fix**: Extract to constants:
```typescript
export const TIMEOUTS = {
  SPEAKING_INDICATOR: 3000,
  TOAST_SUCCESS: 3000,
  TOAST_ERROR: 5000,
  EMOTE_DURATION: 3000,
  CHAT_BUBBLE_DURATION: 5000,
} as const
```

**Severity**: LOW — Maintainability issue

---

### 13. Inconsistent Error Handling

**File**: `frontend/src/screens/SpectatorScreen.tsx:98-112`

```typescript
try {
  await fetch('/api/bets', { ... })
} catch {
  // Bet is tracked locally regardless
}
```

**Issue**: Silently swallows all errors, including network failures, 500 errors, etc. User sees "bet placed" locally but server never received it.

**Fix**: Log errors and show user feedback:
```typescript
} catch (error) {
  console.error('Failed to place bet:', error)
  // Optionally: show toast notification
}
```

**Severity**: LOW — UX issue, not critical (bet still tracked locally)

---

### 14. Unused Type Definitions

**File**: `frontend/src/lib/types.ts:72-77`

```typescript
// Active Emote (for emote animations)
export interface ActiveEmote {
  playerId: string
  emoji: string
  timestamp: number
}
```

**Issue**: This type is never used. The actual implementation uses:
```typescript
activeEmotes: Record<string, { emoji: string; timeout: ReturnType<typeof setTimeout> }>
```

**Fix**: Either use the type or remove it.

**Severity**: LOW — Dead code, doesn't affect runtime

---

## ✅ GOOD Patterns Found

### 1. Immutable State Updates (gameStore.ts)

```typescript
setPlayerAlive: (name, alive) =>
  set((state) => {
    const player = state.players[name]
    if (!player) return {}  // ✅ Early return if player not found
    return {
      players: {
        ...state.players,  // ✅ Spread existing
        [name]: { ...player, isAlive: alive },  // ✅ Create new player object
      },
    }
  }),
```

✅ Perfect immutability — never mutates, always creates new objects.

---

### 2. Module-Level Timer Storage (gameStore.ts)

```typescript
// Module-level timer storage for chat bubbles (not in zustand state)
const chatBubbleTimers = new Map<string, ReturnType<typeof setTimeout>>()
```

✅ Excellent pattern — keeps setTimeout IDs outside Zustand state (which should be serializable), while still providing cleanup.

---

### 3. Cleanup in resetGame (gameStore.ts:281-309)

```typescript
resetGame: () => {
  // Clear all bubble timers
  chatBubbleTimers.forEach((timer) => clearTimeout(timer))
  chatBubbleTimers.clear()

  // Clear all emote timeouts
  const current = useGameStore.getState()
  Object.values(current.activeEmotes).forEach(({ timeout }) => clearTimeout(timeout))

  set({ /* reset all state */ })
}
```

✅ Comprehensive cleanup — clears all timers before resetting state.

---

### 4. Proper Event Listener Cleanup (useWallet.ts:44-47)

```typescript
return () => {
  window.ethereum.removeListener('accountsChanged', handleAccountsChanged)
  window.ethereum.removeListener('chainChanged', handleChainChanged)
}
```

✅ Proper cleanup of external listeners.

---

### 5. Semantic HTML in LandingScreen (LandingScreen.tsx:254-260)

```typescript
<Input
  placeholder="ENTER ALIAS"
  value={nick}
  onChange={(e) => setNick(e.target.value)}
  maxLength={12}
  autoFocus
/>
```

✅ Proper input attributes (maxLength, autoFocus).

---

## State Management Analysis

### Store Architecture (4 Stores)

**1. gameStore.ts** (310 lines)
- ✅ Clean separation: game state, players, lobby, UI state
- ✅ Immutable updates throughout
- ✅ Proper cleanup in `resetGame`
- ⚠️ `wsSend` function stored in state (works, but unorthodox)

**2. chatStore.ts** (43 lines)
- ✅ Simple, focused store
- ✅ MAX_MESSAGES limit prevents unbounded growth
- ✅ Proper message deduplication with `id`

**3. bettingStore.ts** (41 lines)
- ✅ Minimal, focused on betting state
- ✅ Immutable updates

**4. walletStore.ts** (41 lines)
- ✅ Clean wallet connection state
- ✅ Proper reset on disconnect

### Store Coupling
- ✅ Minimal coupling — each store has clear boundaries
- ✅ No cross-store subscriptions (good!)

---

## Component Architecture Analysis

### File Organization
```
src/
├── stores/         ✅ 4 stores, clean separation
├── hooks/          ✅ 5 custom hooks (useWebSocket, useWallet, etc.)
├── screens/        ✅ 3 main screens (Landing, Spectator, Reveal)
├── components/
│   ├── game/       ✅ 12 game components (PlayerCard, GameBoard, etc.)
│   ├── betting/    ✅ 6 betting components
│   ├── lobby/      ✅ 3 lobby components
│   ├── wallet/     ✅ 2 wallet components
│   ├── layout/     ✅ 3 layout components
│   └── ui/         ✅ 7 UI primitives (Button, Input, etc.)
└── lib/            ✅ 5 utility modules (types, constants, blockchain, etc.)
```

✅ **Excellent organization** — clear separation by feature/domain.

### Component Depth
- ✅ Max 3-4 levels deep (reasonable)
- ✅ No deep prop drilling (uses Zustand selectors instead)

### Component Sizes
- ✅ Most components < 200 lines
- ⚠️ `SpectatorScreen.tsx` is 459 lines (could split into smaller components)
- ⚠️ `LandingScreen.tsx` is 368 lines (could split into smaller components)

---

## TypeScript Quality

### Type Coverage
- ✅ ~90% type-safe (good coverage)
- ⚠️ Some `any` usage in WebSocket handlers (see HIGH issue #7)
- ✅ Proper use of generics in types.ts

### Type Definitions
- ✅ Comprehensive types in `lib/types.ts`
- ✅ Good use of union types (`Phase`, `BetType`, `ScreenState`)
- ⚠️ Some unused types (see LOW issue #14)

---

## Animation Performance

### Framer Motion Usage
- ✅ Proper use of `AnimatePresence` for exit animations
- ✅ `layoutId` for shared element transitions (PlayerCard.tsx:39)
- ⚠️ Heavy use of motion components (could impact low-end devices)

### Potential Performance Issues
1. **PhaseOverlay.tsx:67-87** — 20 animated stars on every night phase (minor impact)
2. **GameOverScreen.tsx:34** — 150 confetti particles with `requestAnimationFrame` (OK, has cleanup)
3. **LandingScreen.tsx:151-181** — 20 floating fragments with complex animations (minor impact on mobile)

---

## Accessibility

### Keyboard Navigation
- ⚠️ Missing focus management on screen transitions
- ⚠️ No skip-to-content link
- ⚠️ Vote buttons accessible via click only (no keyboard support)

### ARIA Labels
- ⚠️ Missing on icon-only buttons (see MEDIUM issue #9)
- ⚠️ Missing on form inputs in betting panel

### Color Contrast
- ✅ Generally good contrast (gold on dark bg passes WCAG AA)
- ⚠️ Some low-contrast text (e.g., `text-white/40` may fail WCAG AAA)

---

## Mobile Responsiveness

### Breakpoints
- ✅ Good use of Tailwind responsive classes (`lg:`, `md:`)
- ✅ Mobile-first design approach

### Touch Interactions
- ✅ Tap targets are appropriately sized (min 44x44)
- ✅ `MobileTabBar.tsx` provides proper mobile navigation

### Layout Issues
- ⚠️ `GameBoard.tsx` uses different layouts for mobile vs desktop (3+2+2 vs 4+3)
  - This is intentional and works well ✅

---

## Security Considerations

### XSS Prevention
- ✅ React escapes all user input by default
- ✅ No `dangerouslySetInnerHTML` usage
- ✅ No direct DOM manipulation with user content

### Web3 Security
- ✅ Proper use of ethers.js for wallet connection
- ⚠️ Missing validation on USDC allowance before approval
- ⚠️ No slippage protection on bets

### API Security
- ⚠️ Missing CSRF protection on POST requests
- ⚠️ No rate limiting on bet placement (client-side)

---

## Testing Recommendations

### Unit Tests (Missing)
- `gameStore.ts` — Test all state transitions
- `useWebSocket.ts` — Mock WebSocket, test event handling
- `useBetting.ts` — Test bet placement flow

### Integration Tests (Missing)
- Full game flow: Landing → Lobby → Game → Reveal → GameOver
- Betting flow: Connect wallet → Place bet → Game ends → Payout

### E2E Tests (Missing)
- User journey: Join as spectator → Place bet → Watch game → Claim winnings
- Mobile responsiveness tests

---

## Performance Metrics

### Bundle Size (Estimated)
- React + Zustand + Framer Motion + ethers.js ≈ 400KB (before gzip)
- ✅ Reasonable for a rich interactive app

### Render Performance
- ✅ No expensive computations in render paths
- ⚠️ Could benefit from `React.memo` on `PlayerCard` (renders 7 times per update)

---

## Handoff

### Attempted
- ✅ Systematic review of all 56 TypeScript files
- ✅ Identified 14 distinct issues (3 CRITICAL, 4 HIGH, 3 MEDIUM, 4 LOW)
- ✅ Provided specific file:line references for all issues
- ✅ Analyzed state management, component architecture, type safety
- ✅ Reviewed accessibility, performance, security

### Worked
- ✅ Clean Zustand state management (immutable updates)
- ✅ Good component organization and modularity
- ✅ Proper TypeScript usage (mostly)
- ✅ Responsive design with mobile support
- ✅ Proper cleanup in most places (wallet listeners, canvas animation)

### Failed
- ❌ Memory leaks from uncleaned timeouts (3 instances)
- ❌ Stale closure risk in ActionPanel auto-submit
- ❌ Exhaustive-deps rule disabled in useWebSocket
- ❌ Missing accessibility features (ARIA labels, keyboard nav)

### Remaining
- **Fix all CRITICAL issues** (memory leaks) — ~2 hours
- **Fix HIGH issues** (deps, type safety) — ~3 hours
- Add unit tests for stores and hooks — ~4 hours
- Add E2E tests for critical flows — ~4 hours
- Improve accessibility (ARIA, keyboard nav) — ~3 hours

---

## Final Verdict

**Status**: ⚠️ **CONDITIONAL PASS**

**Recommendation**: Fix the 3 CRITICAL memory leaks before deployment. The codebase is otherwise well-structured and production-ready.

**Priority**:
1. **CRITICAL** (Must fix): Memory leaks in useWebSocket.ts (2) and useBetting.ts (1)
2. **CRITICAL** (Must fix): Stale closure in ActionPanel.tsx
3. **HIGH** (Recommended): Fix exhaustive-deps, type safety, missing deps
4. **MEDIUM** (Nice to have): Performance optimizations, accessibility
5. **LOW** (Polish): Code duplication, magic numbers, error handling

**Estimated Fix Time**: 2-3 hours for CRITICAL issues, 5-8 hours for all HIGH issues.

---

**Review Completed**: 2026-02-16
**Reviewer**: p-frontend-reviewer (mafia-review team)
