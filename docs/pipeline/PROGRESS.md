# MafiaAI Pipeline Progress

## P0 Design - COMPLETE
- DESIGN.md written with full specs
- File ownership map defined
- arb-bot reuse patterns identified

## P1 Implementation - COMPLETE
- Started: 2026-02-11 19:10
- Completed: 2026-02-11 19:36
- Team: p-impl-core (sonnet), p-impl-engine (sonnet), p-test-writer (sonnet), p-impl-betting (sonnet)

### Results
- 40 source files created
- 45 tests passing, 8 skipped (betting stubs)
- 47% overall coverage (core engine modules: 100%)
- Full game loop verified: Night → Day Discussion → Day Vote → repeat → Game Over
- Betting module: pool, odds, oddsmaker implemented

### Fixes Applied by Lead
- Detective investigation results now persist across rounds (known_roles update)
- Agent memory now updates after each phase (rolling 10 events)
- Night phase handlers now use agent memory instead of empty tuple
- Odds regex pattern broadened (supports names with digits/underscores)
- Test fixes: AsyncMock import, MockSettings lambda self param

## Day 1 Goal: Terminal Game ✅
- Game engine state machine works
- 7 AI personalities defined
- Claude API wrapper with Haiku/Sonnet model split
- Mock-verified full game completion

## Day 2: WebSocket + Dashboard ✅
- Completed: 2026-02-11 19:58
- Team: p-impl-api (sonnet), p-impl-ui (sonnet)
- FastAPI + WebSocket server with auto-reconnect
- HTML/CSS/JS dark-theme dashboard (agent cards, chat log, vote display)
- Real-time game spectating verified in browser
- Health endpoint, static file serving, WebSocket connection all working
- 45 tests still passing

## Day 3: Betting Integration ✅
- Completed: 2026-02-11 20:12
- Team: p-integrator (sonnet), p-doc-writer (haiku)
- BettingManager class: pool management, spectator registration, odds blending (70% AI + 30% market)
- WebSocket bet handling: place_bet → bet_confirmed/bet_rejected
- GameEngine hooks: odds update after each phase, settlement on game_over
- REST: /api/odds endpoint
- Dashboard: betting panel with amount selector, bet buttons, chip balance display
- README.md + CLAUDE.md created for hackathon submission
- 45 tests passing, 8 betting stubs still skipped

## Day 4: Tests + Polish — COMPLETE
- Started: 2026-02-11 20:12
- Completed: 2026-02-11
- 82 tests, 66% coverage

## Day 5: Blockchain Integration — IN PROGRESS
- Started: 2026-02-11
- **Phase 1**: LLM Swap (Claude→Kimi) + Smart Contract (parallel)
- **Phase 2**: Backend web3 + Frontend wallet (parallel)
- **Phase 3**: Deploy + E2E

### Phase 1 Status — COMPLETE
| Task | Agent | Status |
|------|-------|--------|
| Swap Claude → Kimi (OpenAI SDK) | p-llm-swap | ✅ Complete (82 tests pass) |
| Smart Contract + Hardhat | p-solidity | ✅ Complete (34 tests pass) |

### Phase 2 Status — COMPLETE
| Task | Agent | Status |
|------|-------|--------|
| Python web3 backend | p-backend-chain-2 | ✅ Complete (91 tests pass, 68% coverage) |
| Frontend wallet UI | p-frontend-chain-2 | ✅ Complete (blockchain.js, wallet UI, claim flow) |

**Phase 2 Deliverables:**
- `src/blockchain/provider.py` — AsyncWeb3 + POA middleware
- `src/blockchain/contract.py` — Oracle ops (create_game, settle, lock_betting)
- `src/api/server.py` — `/api/blockchain-config` endpoint
- `tests/test_blockchain.py` — 9 new tests
- `static/blockchain.js` — MetaMask + ethers.js v6 (330 lines)
- `static/index.html` — Wallet UI, ethers CDN, claim button
- `static/app.js` — Blockchain mode routing in placeBet()
- `static/style.css` — Wallet bar, tx status, claim styles

### Phase 3 Status — COMPLETE
| Task | Agent | Status |
|------|-------|--------|
| Deploy + E2E + docs | p-deploy-qa | ✅ Complete (docs updated, QA PASS) |

**Phase 3 Deliverables:**
- `.env.example` — All environment variables documented
- `README.md` — Updated: Kimi AI, blockchain setup, 125 tests
- `CLAUDE.md` — Updated: architecture, blockchain module, troubleshooting
- `docs/pipeline/QA_REPORT.md` — Status: PASS
- Contract deploy attempted (needs funded wallet — manual step)

## Blockchain Summary
- **125 total tests** (91 Python + 34 Solidity), all passing
- **68% Python coverage**
- **3 phases completed** in pipeline
- **One manual step remaining**: Deploy contract with funded wallet (`npm run deploy:testnet`)

---

## Mixed-Player Arena — P1 Implementation — COMPLETE
- Started: 2026-02-12
- Completed: 2026-02-12
- Team: p-impl-players (sonnet), p-impl-engine (sonnet), p-impl-api (sonnet)

### New Modules Created
- `src/players/` — PlayerProtocol, TurnContext, HouseAIPlayer, MoltbookAgentPlayer, HumanPlayer, AgentHumanPlayer
- `src/lobby/` — LobbyManager (player registration, fill_with_house_ai)
- `src/moltbook/` — MoltbookClient (REST: auth, DM, polling)

### Modified Modules
- `src/config/constants.py` — +PlayerType enum, +BetType.IS_AI_OR_HUMAN, +Phase.REVEAL
- `src/config/settings.py` — +moltbook_api_url, +lobby_timeout_seconds, +human_turn_timeout
- `src/engine/phase_handlers.py` — Refactored from (state, agents, llm_client, cb) to (state, players, agent_states, cb)
- `src/engine/game_engine.py` — Accepts players dict from lobby, REVEAL phase, identity reveals
- `src/betting/manager.py` — +IS_AI_OR_HUMAN pool, +settle_identity_bets()
- `src/api/server.py` — +join_lobby, +action_response WS messages, +Moltbook agent join endpoint
- `src/api/ws_manager.py` — +player_sessions, +send_to_player(), +response futures
- `src/main.py` — Lobby → engine wiring
- `static/index.html` — +lobby UI, +human input forms, +reveal section
- `static/app.js` — +lobby events, +action input, +reveal display
- `static/style.css` — +lobby/input/reveal styles

## Mixed-Player Arena — P2 Verification — COMPLETE
- Status: ✅ PASS
- 154 tests passing, 73% coverage (exceeds 68% baseline)
- 8/8 integration scenarios verified
- See docs/pipeline/QA_REPORT.md for full details

## Mixed-Player Arena — P3 Polish — COMPLETE
- README.md, CLAUDE.md, .env.example updated with new modules and settings

## Previous Pipeline Complete (Mixed-Player Arena)
- 188 total tests (154 Python + 34 Solidity), 73% coverage
- 4 player types, lobby system, identity betting, REVEAL phase

---

## USDC Betting Unification Pipeline

### Goal
Unify 3 fragmented betting systems (chips/MON/USDC) into single USDC-only system.

### Design Doc
See `docs/pipeline/USDC_DESIGN.md`

### P0 Design — COMPLETE
- Architecture finalized: single USDC via x402, Moltbook Identity auth
- File ownership map defined
- All technical decisions documented

### P1 Implementation — COMPLETE
- Started: 2026-02-14
- Team: p-impl-backend (sonnet), p-impl-contract (sonnet), p-test-writer (sonnet)

#### p-impl-contract (Smart Contract + Frontend)
- ✅ `contracts/MafiaBetting.sol` — Rewritten for USDC ERC-20 (SafeERC20, approve+transferFrom)
- ✅ `contracts/MockERC20.sol` — Created for Hardhat tests
- ✅ `test/MafiaBetting.test.js` — 39 tests passing
- ✅ `static/blockchain.js` — USDC approval flow, 6 decimals
- ✅ `scripts/deploy.js` — USDC address parameter

#### p-impl-backend (Python Backend)
- ✅ `src/moltbook/auth.py` — NEW: MoltbookAuth with JWT verify_identity()
- ✅ `src/betting/settlement.py` — NEW: USDCSettlement (web3.py ERC-20 transfers)
- ✅ `src/betting/manager.py` — REWRITTEN: unified place_bet(USDC), no chips
- ✅ `src/models/betting.py` — Bet: tx_hash required, payment_method removed
- ✅ `src/config/settings.py` — +moltbook_app_key, +settlement_enabled, -starting_chips
- ✅ `src/config/constants.py` — +MIN/MAX_BET_USDC, -DEFAULT_STARTING_CHIPS
- ✅ `src/api/server.py` — Moltbook Identity auth, unified /api/bets, WS redirect
- ✅ `src/x402/middleware.py` — Simplified (no test mode fallback)
- ✅ `src/engine/game_engine.py` — Settlement hook
- ✅ `src/ai_bettor/client.py` — REST /api/bets endpoint

#### p-test-writer + Lead (Test Suite)
- ✅ `tests/test_moltbook_auth.py` — NEW: 11 tests (100% coverage)
- ✅ `tests/test_settlement.py` — NEW: 10 tests (86% coverage)
- ✅ `tests/test_betting.py` — REWRITTEN: 29 tests, USDC-only
- ✅ `tests/test_x402_betting.py` — REWRITTEN: 16 tests, unified API
- ✅ `tests/test_api.py` — UPDATED: WebSocket redirect, Moltbook Identity
- ✅ `tests/test_x402.py` — All passing

### P2 Verification — COMPLETE
- **236 Python tests + 39 Hardhat tests = 275 total**, ALL PASSING
- **72% Python coverage** (moltbook/auth: 100%, models: 100%, betting/manager: 90%)
- Zero import errors, zero syntax errors

## Previous Pipeline Complete (Frontend Redesign)

---

## MAFI_AI_FRONT UI Merge Pipeline

### Goal
Merge MAFI_AI_FRONT branch visual design into main's real WebSocket architecture.

### P1 Implementation — COMPLETE
- Started: 2026-02-16
- Completed: 2026-02-16
- Team: p-impl-core (sonnet), p-impl-ui (sonnet), p-impl-bet (sonnet)

### Phase Status
- [x] P1a: Foundation (p-impl-core) — types, constants, store, App, useWebSocket, globals.css, server.py
- [x] P1b: Visual Components + Screens (p-impl-ui) — LandingScreen, SpectatorScreen, RevealScreen, components
- [x] P1c: Betting Integration (p-impl-bet) — BettingPanel, wallet, spectator betting
- [x] P2: Verification — build passes (0 errors), 236 backend tests pass

### Changes Summary (28 files, +517/-355)

**New files created:**
- `frontend/public/images/` — 13 image assets (character portraits, backgrounds, logo)
- `frontend/src/screens/LandingScreen.tsx` — 368 lines, shattered mask effect, avatar selection, wallet connect
- `frontend/src/screens/SpectatorScreen.tsx` — 220 lines, real WebSocket spectating + betting panel
- `frontend/src/screens/RevealScreen.tsx` — 149 lines, 3D card flip reveal
- `frontend/src/components/game/RoleRevealModal.tsx` — 115 lines, dramatic role reveal at game start
- `frontend/src/components/game/NightOverlay.tsx` — 39 lines, night phase transition
- `frontend/src/components/game/BettingStatusBar.tsx` — 48 lines, floating odds bar
- `frontend/src/components/ui/Input.tsx` — 26 lines, gold-themed input

**Modified files:**
- `gameStore.ts` — +screen routing, nickname, avatarIndex, isSpectator, emotes, resetGame
- `useWebSocket.ts` — +spectator support, screen transitions, identity reveal handling
- `App.tsx` — screen-based routing (landing→lobby→game→spectate→reveal→game_over)
- `types.ts` — +ScreenState, avatarIndex, ActiveEmote
- `constants.ts` — +AVATAR_IMAGES, avatarIndex per agent
- `globals.css` — +Outfit font, gold theme vars, text-glow utilities
- `server.py` — +/images static mount
- `GameOverScreen.tsx` — canvas confetti, redesigned win/lose card, play again/reset
- `PlayerCard.tsx`, `GameBoard.tsx` — avatar images
- `LobbyScreen.tsx`, `PlayerSlot.tsx` — avatar cards, progress styling
- `Header.tsx`, `GameLayout.tsx` — gold branding, BettingStatusBar, NightOverlay
- `BettingPanel.tsx`, `OddsBar.tsx`, `BetSlip.tsx`, `BetHistory.tsx`, `PayoutCard.tsx`, `SuspectList.tsx` — gold theme
- `ConnectButton.tsx`, `TxToast.tsx` — gold theme
- `Button.tsx` — +gold variant
- `GlassCard.tsx` — +blur variants

### Build Output
- 0 TypeScript errors
- 3 JS chunks + 1 CSS: index.js (273KB), ethers.js (269KB), framer-motion.js (125KB), index.css (71KB)
- 236 Python backend tests pass, 0 failures

## Pipeline Complete — USDC Betting Unification

### Final Summary — USDC Betting Unification
- **275 total tests** (236 Python + 39 Solidity), all passing
- **72% Python coverage**
- **Single USDC currency** — chips removed entirely, MON for gas only
- **Moltbook Identity auth** — JWT-based via X-Moltbook-Identity header
- **Unified /api/bets endpoint** — all bets via x402 USDC payment
- **USDC ERC-20 smart contract** — SafeERC20, approve+transferFrom pattern
- **Server-side settlement** — USDCSettlement class for web3.py USDC transfers
- **WebSocket spectating only** — betting redirected to REST API
- **MIN $1 / MAX $100** — USDC bet limits enforced

---

## Frontend Redesign — React + TypeScript + Tailwind

### Goal
Replace vanilla HTML/CSS/JS SPA with modern React 19 + TypeScript + Vite + Tailwind + Framer Motion frontend.

### P1 Implementation — COMPLETE
- Started: 2026-02-14
- Completed: 2026-02-14
- Team: p-impl-core (sonnet), p-impl-ui (sonnet), p-impl-bet (sonnet)

| Agent | Status | Files Created | Focus |
|-------|--------|:---:|-------|
| p-impl-core | ✅ DONE | 16 | Project setup, stores, hooks, WebSocket, types |
| p-impl-ui | ✅ DONE | 26 | Game UI components, layout, animations |
| p-impl-bet | ✅ DONE | 13 | Betting panel, wallet, blockchain integration |

### Integration Fixes (Lead)
- WebSocket message format: `type` field (not `event_type`) for client→server
- Event handler field names: `agent` not `eliminated`, `name` not `player_name`
- BettingPanel integrated into GameLayout (desktop + mobile tabs)
- ConnectButton integrated into Header
- TxToast added to App root
- Code splitting: ethers.js + framer-motion as separate chunks

### Build Results
- **48 TypeScript source files** created
- **0 TypeScript errors** (`tsc --noEmit` clean)
- **Build output**: 3 JS chunks + 1 CSS
  - `index.js` — 244KB (74KB gzip) — app code
  - `ethers.js` — 269KB (98KB gzip) — blockchain lib
  - `framer-motion.js` — 125KB (41KB gzip) — animation lib
  - `index.css` — 43KB (8KB gzip) — Tailwind styles

### Architecture
- **React 19** + TypeScript strict mode
- **Vite 6** with HMR, dev proxy to FastAPI :8080, build to `../static`
- **Tailwind CSS v4** (CSS-first `@theme` config)
- **Zustand** stores: gameStore, chatStore, bettingStore, walletStore
- **Framer Motion** for phase overlays, card animations, tab transitions
- **ethers.js v6** for MetaMask + Monad testnet + USDC contract
- **15 WebSocket event types** routed to stores
- **7 CSS-art character avatars** (no external images)
- **Mobile-first** with 3-tab bottom navigation
- **Desktop** 3-column layout (players | chat | betting)

## Pipeline Complete — Frontend Redesign

---

## JS Frontend Docs Update — 2026-02-18

### Task #1 — Update English Docs (p-docs-en)

**Files Modified:**
- `docs/USERFLOW.md` — Full rewrite reflecting JS branch frontend rewrite
- `README.md` — Targeted updates

**Changes:**
1. Module Responsibility Map: replaced 37-file modular layout with flat structure (screens/, components/, store.ts, websocket.ts, types.ts, mappers.ts, constants.ts)
2. Player Interaction Flow: wallet → nickname → avatar selection → "Enter Lobby" flow; `join_lobby` has no player_type field
3. Human Player Actions: NIGHT = Moon overlay + text; DAY_VOTE = click player cards; DAY_DISCUSSION = ChatBoard with "Your Turn to Speak"
4. Role Reveal Modal: new section documenting fullscreen modal at game start
5. WebSocket: `join_lobby {type, name}` (no type field), ping at 25s
6. Screen State Machine: updated LANDING sub-states, ScreenState.SPECTATE as distinct state
7. UI Component Tree: completely rewritten for flat architecture; BettingPanel is null stub; SpectatorScreen has inline Betting Terminal (380px)
8. State Management: 4 separate stores → 1 unified GameState interface; State Transitions table added
9. Phase Transitions: CSS transition-opacity not framer-motion; NightOverlay = Moon icon + text
10. Desktop layout: 3-column → 2-section (board + 340px ChatPanel); Spectator = board + 380px BettingTerminal
11. Mobile layout: MobileTabBar removed; FAB + slide-in ChatBoard drawer

**README.md targeted edits:**
- Features: "Responsive Design" updated (2-section + FAB drawer); "Modern React Frontend" updated (flat, 1 store)
- Architecture: frontend directory tree replaced with flat structure
- Key Files: hooks/useWebSocket.ts + stores/gameStore.ts → store.ts, websocket.ts, GameScreen.tsx etc.
- Zustand "4 stores" → "1 unified store"
- Client→Server WS events updated

## Handoff (Task #1)
- **Attempted**: Full USERFLOW.md rewrite + targeted README.md edits
- **Worked**: All sections verified against actual source (store.ts, App.tsx, all screens, GameComponents.tsx, websocket.ts, types.ts, constants.ts, mappers.ts)
- **Failed**: Nothing
- **Remaining**: Task #2 — Korean docs (USERFLOW.ko.md + README.ko.md) need same updates in Korean

### Task #2 — Update Korean Docs (p-docs-ko)

**Files Modified:**
- `docs/USERFLOW.ko.md` — Full rewrite matching updated English USERFLOW.md
- `README.ko.md` — Targeted updates matching updated English README.md

**Changes (USERFLOW.ko.md):**
1. Module Responsibility Map: replaced old modular layout (37 files, multiple stores, hooks) with flat structure (screens/, components/, store.ts, websocket.ts, types.ts, mappers.ts, constants.ts) — translated to Korean
2. Player Interaction Flow (sequence diagram): updated to wallet connect → nickname → avatar selection → "Enter Lobby" flow; `join_lobby` has no player_type field
3. Human Player Actions table: updated NIGHT (Moon overlay), DAY_VOTE (click player cards), DAY_DISCUSSION (ChatBoard "Your Turn to Speak") with full detail
4. Role Reveal Modal: new section added and translated
5. Spectator Screen Layout: replaced simple list with full ASCII art layout (Korean labels)
6. WebSocket events: updated to 15 server→client events with UI effects; 3 client→server events (ping at 25s)
7. Screen State Machine: updated LANDING sub-states (wallet→nickname→avatar), ScreenState.SPECTATE as distinct state
8. UI Component Tree: completely rewritten for flat architecture with Korean labels
9. State Management: 4 separate stores → 1 unified GameState TypeScript interface with Korean comments
10. Phase Transitions: CSS transition-opacity (not framer-motion); NightOverlay = Moon icon + NIGHT PHASE text
11. Desktop layout: 3-column → 2-section (board + 340px ChatPanel); Spectator = board + 380px BettingTerminal
12. Mobile layout: MobileTabBar removed; FAB + slide-in ChatBoard drawer
13. Troubleshooting: added 2 new entries (auto-transition, chat not sending)

**Changes (README.ko.md):**
- Features: "모던 React 프론트엔드" updated (flat, 1 unified store); "반응형 디자인" updated (2-section + FAB drawer); "비주얼 폴리시" updated (Role Reveal modal, Night Phase overlay)
- Lobby System: updated to include wallet connect → nickname → avatar flow
- Architecture: frontend directory tree replaced with flat structure (6 screens, 2 component files, 1 store)
- Key Design Patterns: updated to mention single Zustand store
- Key Files: updated frontend files (store.ts, websocket.ts, screens/, GameComponents.tsx)

## Handoff (Task #2)
- **Attempted**: Full Korean translation of updated English docs
- **Worked**: Both files fully updated; natural Korean prose throughout; code blocks, file paths, URLs kept in English; Mermaid diagrams preserved with Korean node labels where appropriate
- **Failed**: Nothing
- **Remaining**: None — Korean docs now match English versions

---

## Blockchain V2 Foundation — 2026-02-18

### Goal
Fix broken blockchain layer: V2 contract (commit-reveal, 4 bet types), Python gateway, player wallets, betting manager cleanup.

### P1 Implementation — COMPLETE
- Started: 2026-02-18
- Team: p-impl-solidity (sonnet), p-impl-python (sonnet), p-test-writer (sonnet)

| Agent | Files | Status |
|-------|-------|--------|
| p-impl-solidity | MafiaBettingV2.sol, test/MafiaBettingV2.test.js, scripts/deploy-v2.js | ✅ 51 Hardhat tests |
| p-impl-python | 13 source files (provider, gateway, players, betting, engine, main) | ✅ 246 existing tests pass |
| p-test-writer | 5 test files (test_gateway new, 4 updated) | ✅ 281 total Python tests |

### Results
- **281 Python tests + 90 Hardhat tests (51 V2 + 39 V1) = 371 total**, ALL PASSING
- **73% Python coverage** (up from 72%)
- ImportError fixed: `create_web3_provider()` exists
- `Bet.tx_hash` now optional (str | None = None)
- All 4 player types have `wallet_address: str | None`
- `BettingManager.reset(new_game_id)` clears pools between games
- `BlockchainGateway` replaces direct `MafiaBettingContract` usage
- V2 contract: commit-reveal, 4 BetType enum, oracle-attested settlement, 7-day refunds
- V1 contract untouched, V1 tests still pass

## Pipeline Complete

---

## Game Flow Redesign — 2026-02-18

### Goal
Remove wallet connection, simplify onboarding to single step, add server game loop.

### P1 Implementation — COMPLETE
- Started: 2026-02-18
- Team: p-impl-backend (sonnet), p-impl-frontend (sonnet)

### Backend Changes (p-impl-backend)
| File | Changes |
|------|---------|
| `src/lobby/manager.py` | +player_metadata, +first_join_time, +reset(), +get_lobby_status(), join() accepts metadata |
| `src/api/ws_manager.py` | +clear_sessions() |
| `src/api/server.py` | Parse avatar_index in join_lobby, structured lobby_status broadcast, +rejoin_lobby handler |
| `src/main.py` | Replaced single-shot start_game_when_ready() with continuous game_loop() (while True) |
| `tests/test_lobby.py` | +8 tests: metadata, reset, first_join_time, get_lobby_status |
| `tests/test_api.py` | +3 tests: avatar_index parsing, rejoin_lobby, clear_sessions |

### Frontend Changes (p-impl-frontend + lead fixes)
| File | Changes |
|------|---------|
| `frontend/src/store.ts` | Removed wallet state/actions, +avatar_index in join_lobby, +playAgain(), structured lobby_status parser, +new_lobby handler |
| `frontend/src/mappers.ts` | buildPlayerFromName() accepts optional avatarIndex param |
| `frontend/src/screens/LandingScreen.tsx` | Single-step onboarding (nickname + avatar on same screen), removed wallet gate |
| `frontend/src/screens/GameOverScreen.tsx` | "Play Again" → playAgain(), "Back to Home" → resetGame(), removed chip balance |

### Results
- **246 Python tests**, all passing (10 new tests)
- **0 TypeScript errors**, frontend build succeeds
- Server game loop: IDLE → LOBBY_WAITING → GAME → COOLDOWN → repeat
- Frontend flow: LANDING → LOBBY → GAME → GAME_OVER → (Play Again → LOBBY | Back to Home → LANDING)

## Pipeline Complete

---

## Phase 2: Wire Frontend Betting, Deprecate V1, X402 Signing, Deploy Prep — 2026-02-18

### Goal
Fix 4 remaining issues: frontend betting not wired, V1 dead code, AI Bettor can't sign X402, V2 deploy scripts missing.

### P1 Implementation — COMPLETE
- Started: 2026-02-18
- Team: p-impl-frontend (sonnet), p-impl-python (sonnet), p-test-writer (sonnet)

| Agent | Files | Status |
|-------|-------|--------|
| p-impl-frontend | frontend/src/store.ts | Done |
| p-impl-python | server.py, client.py, main.py, contract.py (deleted), package.json | Done |
| p-test-writer | test_api.py, test_ai_bettor.py, test_blockchain.py, CLAUDE.md | Done |

### Changes
1. **Frontend betting wired** — `placeBetUSDC()` in store.ts now sends `sendWS({ type: 'place_bet', ... })` after local state update
2. **WS bet processing** — server.py `place_bet` handler calls `betting_manager.place_bet()`, sends `bet_confirmed`/`bet_rejected`
3. **V1 contract deleted** — `src/blockchain/contract.py` removed, `TestMafiaBettingContract` removed (-2 tests)
4. **X402 transport** — AIBettorClient accepts `private_key`, creates x402 httpx client for auto 402 handling
5. **V2 deploy scripts** — `deploy-v2:testnet` and `deploy-v2:local` added to package.json
6. **main.py** — passes `private_key` from settings to AIBettorClient

### Test Results
- **308 Python tests**, all passing
- **90 Hardhat tests** (unchanged)
- **398 total tests**

---

## Comprehensive Refactoring Pipeline — 2026-02-19

### Goal
Transform codebase from 6.9/10 to 8.0+/10: dead code removal, bug fixes, backend/frontend restructuring. Zero behavior change.

### P0 Design — COMPLETE
- REFACTOR_DESIGN.md written
- File Ownership Map: p-impl-backend (src/), p-impl-frontend (frontend/src/), p-test-writer (tests/)

### P1 Implementation — COMPLETE
- Started: 2026-02-19
- Team: p-impl-backend (sonnet), p-impl-frontend (sonnet), test fixes by team-lead
- Note: Team lead session crashed mid-pipeline. Recovered in new session — backend agent was stuck on permission approval, frontend agent completed autonomously.

| Agent | Track | Status |
|-------|-------|--------|
| p-impl-backend | Phase 1A/1B + Phase 2 | ✅ Complete |
| p-impl-frontend | Phase 1C/1D + Phase 3 | ✅ Complete |
| team-lead (recovery) | Fix broken tests (was p-test-writer task) | ✅ Complete |

**p-impl-frontend deliverables** (0 TypeScript errors, `npm run build` ✅):
- Phase 1C: Removed ethers + recharts (45 packages), cleaned vite.config.ts, deleted null BettingPanel
- Phase 1D: AVATAR_IMAGES/AVATAR_COUNT moved from types.ts → constants.ts (4 import sites updated)
- Phase 3A: Extracted GamePlayerCard.tsx, ChatBoard.tsx; created shared/ (GameBackground, PhaseIndicator, GameHeader, PlayerGrid)
- Phase 3B: Created 4 hooks (useChatBubbles, useCountdown, useNightOverlay, useActionTimeout)
- Phase 3C: Sliced store.ts (560L) → store/ (gameSlice, bettingSlice, connectionSlice, uiSlice, index with 5 selectors)
- Phase 3D: Created types/events.ts (ServerEvent 16 variants, ClientEvent 5 variants); typed websocket.ts

See: docs/pipeline/REFACTOR_FRONTEND.md

**p-impl-backend deliverables** (371 Python tests passing, 88% coverage):
- Phase 1A: Deleted src/storage/ (5 files), src/utils/errors.py, GameConfig from models/game.py
- Phase 1B: Fixed await-on-sync bug (server.py), removed oddsmaker mafia count leak
- Phase 2A: Split server.py (560→90 lines) into validators.py, bet_routes.py, lobby_routes.py, ws_handler.py
- Phase 2B: Extracted game_engine game-over into 4 private methods
- Phase 2C: Replaced routes.py globals with app.state; updated main.py and test_api.py

See: docs/pipeline/REFACTOR_BACKEND.md

**Test fixes** (team-lead recovery):
- Deleted tests/test_errors.py (21 tests), tests/test_storage.py (22 tests)
- Cleaned test_utils.py (removed TestErrorHierarchy, 11 tests)
- Updated test_api.py (12 tests: routes.set_* → client.app.state.*)

### Test Results
- **371 Python tests**, all passing (88% coverage)
- **90 Hardhat tests** (unchanged)
- **461 total tests**
- **Frontend**: 0 TypeScript errors, npm run build ✅

---

## Refactoring Phase 2 — Shared Component Integration — 2026-02-19

### Goal
Integrate shared components (GameBackground, GameHeader, PhaseIndicator, PlayerGrid) into SpectatorScreen and GameScreen. Fix `as any` in gameSlice. Update CLAUDE.md stale references.

### P1 Implementation — COMPLETE
- Started: 2026-02-19
- Team: p-impl-screens (sonnet), p-doc-updater (haiku)

| Agent | Files | Status |
|-------|-------|--------|
| p-impl-screens | SpectatorScreen.tsx, GameScreen.tsx, gameSlice.ts | ✅ Complete |
| p-doc-updater | CLAUDE.md | ✅ Complete |

### Changes
**Screen Integration:**
1. SpectatorScreen: 606 → 572 lines — GameBackground, GameHeader+PhaseIndicator, PlayerGrid replace inlined blocks
2. GameScreen: 353 → 309 lines — same 3 shared components integrated
3. GamePlayerCard removed from both screens (now behind PlayerGrid)
4. Sun/Moon imports removed (PhaseIndicator handles them)

**gameSlice.ts:**
5. `event as any` removed — `eventType` uses `'event_type' in event` narrowing
6. `data` kept as `any` with eslint-disable (discriminated union needed for full fix — separate task)

**CLAUDE.md:**
7. Removed stale `src/storage/` and `errors.py` references
8. Added new API modules (validators, bet_routes, lobby_routes, ws_handler)
9. Expanded frontend file structure (store/, hooks/, components/shared/, types/events.ts, mappers.ts)
10. Updated test counts: 371 Python, 90 Solidity, 461 total, 88% coverage

### P2 Verification — COMPLETE (PASS)
- 371 Python tests passing
- 0 TypeScript errors, frontend build clean
- All 4 shared components imported in both screens
- GamePlayerCard: 0 direct refs in screens
- CLAUDE.md: 0 storage/errors.py refs, new modules present
- See: docs/pipeline/QA_REPORT_V2.md

### Notes
- Original plan targeted ≤400/≤200 lines — the 3 described replacements save ~35 lines each. Hitting lower targets requires extracting betting panel (~250L), spectator chat (~100L), and modals (~140L) into new components — a follow-up task.

## Pipeline Complete

---

## Code Quality Refactoring — 2026-02-19

### Goal
Comprehensive code quality refactoring: security fixes, backend file splits, frontend component extraction. Zero behavior change.

### Phase 1: Critical & Security Fixes — COMPLETE
- Team: p-impl-security (sonnet)
- 5 fixes: AI Bettor immutability (list→tuple), X402 amount extraction, WebSocket validation, API error handling, blockchain gateway bounds
- Report: docs/pipeline/P1_SECURITY_FIXES.md

### Phase 2: Backend Refactoring — COMPLETE
- Team: p-impl-backend (sonnet)
- main.py split → main.py + cli/terminal.py
- phase_handlers.py (384L) → phase_night.py + phase_day.py + phase_vote.py + re-export shim
- LLM _parse_odds robustness (clamping warnings, missing key defaults)
- Moltbook Agent send_dm timeout (asyncio.wait_for)
- Game engine blockchain_lock_failed → log.error
- 21 new tests (test_llm_client.py, test_bet_routes.py)
- Report: docs/pipeline/P2_BACKEND_REFACTOR.md

### Phase 3: Frontend Refactoring — COMPLETE
- Team: p-impl-frontend (sonnet)
- SpectatorScreen (573→155L) → BettingPanel.tsx + SpecChatPanel.tsx
- GameScreen (310→165L) → NightOverlay.tsx + NightActionPanel.tsx + RoleRevealModal.tsx
- ErrorBoundary.tsx added, App.tsx wrapped
- constants/timing.ts centralized (6 magic numbers replaced)
- WebSocket error logging (DEV mode)
- Bet input client validation
- XSS check: no dangerouslySetInnerHTML found
- Report: docs/pipeline/P3_FRONTEND_REFACTOR.md

### Phase 4: Verification & Documentation — COMPLETE
- Team: p-qa (sonnet)
- 392 Python tests, all passing, 84% coverage
- Frontend build: PASS (0 TypeScript errors)
- CLAUDE.md updated (file structure, test counts)
- QA verdict: PASS
- Report: docs/pipeline/QA_REPORT_REFACTOR.md

### Test Results
- **392 Python tests**, all passing (84% coverage)
- **90 Hardhat tests** (unchanged)
- **482 total tests**
- **Frontend**: 0 TypeScript errors, npm run build ✅

## Pipeline Complete

---

## Phase 3: Bug Fixes, Coverage Improvement, Feature Completion — 2026-02-18

### Goal
Fix all remaining issues: frontend memory leaks, test coverage gaps (80%→89%), AI Bettor completion, Moltbook join route, X402 field verification, config cleanup.

### P1 Implementation — COMPLETE
- Started: 2026-02-18
- Team: p-impl-frontend (sonnet), p-impl-python (sonnet), p-test-writer (sonnet)

| Agent | Files | Status |
|-------|-------|--------|
| p-impl-frontend | SpectatorScreen.tsx, GameScreen.tsx, store.ts | Done |
| p-impl-python | client.py, server.py, middleware.py, gateway.py, .env.example, CLAUDE.md | Done |
| p-test-writer | 5 new test files + 3 updated test files | Done |

### Changes
**Frontend:**
1. **3 CRITICAL memory leaks fixed** — setTimeout cleanup in SpectatorScreen (activeSpeaker, betSuccess), GameScreen (activeSpeaker)
2. **2 store timeout leaks fixed** — game_over 15s + emote 3s timeouts tracked and cleared in resetGame/playAgain

**Python Source:**
3. **AI Bettor total_won** — handles usdc_settlement/bet_confirmed/bet_rejected events, immutable state
4. **Moltbook lobby join** — POST /api/lobby/join-moltbook for external AI agent registration
5. **X402 field fix** — VerifyResponse.payer (not .payload.get("from")), SettleResponse.transaction
6. **relay_bet() deleted** — placeholder removed from BlockchainGateway
7. **.env.example created** — all configuration variables documented
8. **STARTING_CHIPS removed** from CLAUDE.md (not in Settings)

**Test Coverage (80% → 89%):**
9. game_engine.py: 18% → 99% (+25 integration tests)
10. storage/: 0% → 100% (+24 tests)
11. errors.py: 0% → 100% (+22 tests)
12. retry.py: 52% → 100% (+12 tests)
13. ws_manager.py: 62% → 100% (+27 tests)
14. AI Bettor event tests (+7), Moltbook route tests (+5)
15. Stale test_relay_bet_returns_none removed

### Test Results
- **430 Python tests**, all passing
- **90 Hardhat tests** (unchanged)
- **520 total tests**
- **89% Python coverage** (up from 80%)

## Pipeline Complete
