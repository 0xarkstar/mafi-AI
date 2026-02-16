# Visual Polish Pipeline Progress

## Overview
Bring ~15 interactive visual features from MAFI_AI_FRONT branch into main, wired to real WebSocket data.

## P1 Implementation Phase

### Agents
| Agent | Files | Status |
|-------|-------|--------|
| p-impl-cards | PlayerCard.tsx, GameBoard.tsx, EmoteMenu.tsx (new) | COMPLETE |
| p-impl-spectator | SpectatorScreen.tsx, BettingStatusBar.tsx | COMPLETE |
| p-impl-enhance | gameStore.ts, useWebSocket.ts, GameLayout.tsx, globals.css | COMPLETE |

### Timeline
- Started: 2026-02-16
- Completed: 2026-02-16

## Pipeline Complete

### Verification Results
- **TypeScript**: 0 errors (`tsc --noEmit` clean)
- **Vite Build**: 2133 modules, 0 errors
- **Backend Tests**: 236 passed, 0 failed

### Features Delivered

**HIGH Priority (all implemented):**
1. Character portrait images on PlayerCard (replacing CSS-art PlayerAvatar)
2. Chat bubbles above PlayerCard (AnimatePresence, gold border, 5s auto-dismiss via store)
3. Emote floating display (spring animation, scale 0.5→1.2, glow drop-shadow)
4. Vote overlay + vote count badge (red tint + Target icon, red pill badge)
5. Day/night background crossfade (dual images, 2s CSS transition)
6. SpectatorScreen betting terminal (type selector, target dropdown, quick amounts, payout calc, my bets)
7. EmoteMenu picker (4×2 grid, 8 emojis, animated backdrop)
8. Enhanced speaking gold glow (scale-105, inset shadow, box-shadow 25px)

**MEDIUM Priority (all implemented):**
9. Phase-tinted overlays (NIGHT blue, DAY_VOTE red, default amber)
10. Role badge icons (Sword mafia, Eye detective, Shield citizen)
11. BettingStatusBar animation (cycling width, 5s loop)
12. Spectator chat panel (spring-animated, unread count badge)
13. Game log in SpectatorScreen (last 15 messages, type-colored)

### Visual QA (Playwright)
- **Day phase**: Portrait images, role badges, vote count badges, chat bubbles inside cards ✅
- **Night phase**: Background crossfade to dark blue/purple, stars, moon overlay ✅
- **Day vote phase**: Red tint overlay, "Voting Time" ballot overlay ✅
- **SpectatorScreen**: Full betting terminal (4 bet types, quick amounts, payout calc, My Bets) ✅
- **Spectator Chat**: Toggle panel with "watching" indicator ✅
- **Live Market Feed**: Scrolling ticker with phase/pool/player info ✅

### Bug Fixes (post-implementation)
- `PlayerCard.tsx`: Added `h-full` to click-wrapper div (GlassCard collapsed to 2px)
- `PlayerCard.tsx`: Repositioned chat bubble from above-card (`bottom-full`) to inside-card overlay (`top-1`) — sidebar `overflow-y-auto` was clipping external elements
- `gameStore.ts`: Added `activeEmotes` timeout cleanup in `resetGame()` (memory leak)
- `SpectatorScreen.tsx`: Added NaN/negative guard on amount input

### Files Changed
- `frontend/src/components/game/PlayerCard.tsx` — Major rewrite (portrait images, overlays)
- `frontend/src/components/game/GameBoard.tsx` — Store wiring for new props
- `frontend/src/components/game/EmoteMenu.tsx` — NEW (emoji picker)
- `frontend/src/screens/SpectatorScreen.tsx` — Expanded betting terminal
- `frontend/src/components/game/BettingStatusBar.tsx` — Animated bar + center tick
- `frontend/src/stores/gameStore.ts` — chatBubbles, voteCounts, showVoteUI state
- `frontend/src/hooks/useWebSocket.ts` — Wired agent_message→bubbles, votes, phase→UI
- `frontend/src/components/layout/GameLayout.tsx` — Day/night crossfade, phase overlays
- `frontend/src/styles/globals.css` — Phase tint utility classes
