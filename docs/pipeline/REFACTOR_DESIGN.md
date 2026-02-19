# MafiaAI Comprehensive Refactoring — Design

## Scope
Transform codebase from 6.9/10 to 8.0+/10 without changing external behavior.

## Phase 1: Dead Code Removal + Critical Bug Fixes

### 1A. Delete dead Python packages
- `src/storage/` (entire package) + `tests/test_storage.py`
- `src/utils/errors.py` + `tests/test_errors.py` + `TestErrorHierarchy` from `tests/test_utils.py`
- `src/models/game.py:11-18` (`GameConfig` class, zero imports)

### 1B. Fix critical bugs
- `src/api/server.py:222`: Remove `await` on sync `lobby_manager.join()`
- `src/betting/oddsmaker.py:119-126`: Remove `mafia_alive`/`total_mafia` lines from `_build_game_summary()`

### 1C. Remove dead frontend dependencies
- `npm uninstall ethers recharts`
- Remove ethers manual chunk from `frontend/vite.config.ts:13`
- Delete `BettingPanel` stub in `GameComponents.tsx:402-405`

### 1D. Move misplaced constants
- Move `AVATAR_IMAGES`, `AVATAR_COUNT` from `frontend/src/types.ts:36-46` to `frontend/src/constants.ts`

## Phase 2: Backend Restructuring

### 2A. Split `server.py` (560→~100 lines)
| Content | Target |
|---------|--------|
| `validate_player_name()` (1-31) | `src/api/validators.py` (NEW) |
| `GET /api/blockchain-config` (78-87) | `src/api/routes.py` (existing) |
| `POST /api/bets` (90-168) | `src/api/bet_routes.py` (NEW) |
| `POST /api/lobby/*` (171-307) | `src/api/lobby_routes.py` (NEW) |
| `websocket_endpoint()` (339-558) | `src/api/ws_handler.py` (NEW) |
| `create_app()` + static (34-75, 309-336) | **Stays in `server.py`** |

Key: `ws_manager` → `app.state.ws_manager`. WS `join_lobby`/`rejoin_lobby` → merge into `_handle_lobby_join(ws, data, is_rejoin=False)`.

### 2B. Extract game_engine game-over handling
- `_handle_game_over(winner)` — orchestrator
- `_broadcast_game_over(winner, payouts)` — game_over event
- `_broadcast_reveals(players)` — identity reveals
- `_settle_payouts(combined_payouts)` — V2/legacy settlement

### 2C. Replace `routes.py` mutable globals with `app.state`

## Phase 3: Frontend Restructuring

### 3A. Extract shared components
- `GameBackground`, `PhaseIndicator`, `GameHeader`, `PlayerGrid` → `shared/`
- Split `GameComponents.tsx`: `GamePlayerCard`, `ChatBoard` → own files

### 3B. Extract custom hooks
- `useChatBubbles`, `useCountdown`, `useNightOverlay`, `useActionTimeout` → `hooks/`

### 3C. Slice Zustand store (560→~50 index + 4 slices)
- `gameSlice`, `bettingSlice`, `connectionSlice`, `uiSlice`
- Add selectors: `selectAlivePlayers`, `selectHumanPlayer`, etc.

### 3D. Type WebSocket events
- `ServerEvent` (16 types) + `ClientEvent` (5 types) discriminated unions
- Replace all `any` in WS layer

## File Ownership Map
- `p-impl-backend`: `src/` (all Python source), deleting `src/storage/`, `src/utils/errors.py`
- `p-impl-frontend`: `frontend/src/` (all TypeScript/React)
- `p-test-writer`: `tests/` (all Python tests)
