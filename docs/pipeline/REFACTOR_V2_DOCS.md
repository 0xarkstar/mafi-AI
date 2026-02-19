# CLAUDE.md Refactor V2 — Documentation Updates

## Summary

Successfully updated CLAUDE.md to reflect Phase 1 API refactoring and new test structure.

## Changes Made

### 1. Core Modules Table (lines 85-105)
- **Removed**: `src/storage/` row (aiosqlite, migrations, repositories)
- **Added**: Four new API module rows:
  - `src/api/validators.py` — Request validation (Pydantic schemas)
  - `src/api/bet_routes.py` — Betting REST endpoints
  - `src/api/lobby_routes.py` — Lobby REST endpoints
  - `src/api/ws_handler.py` — WebSocket message handler
- **Simplified**: `src/utils/` description (removed error hierarchy reference)

### 2. File Structure Tree — API Section (lines 557-565)
- **Replaced** generic `server.py` description with specifics: "FastAPI app factory + static files (90 lines)"
- **Updated routes.py** description: "Game REST endpoints" (from generic "REST endpoints")
- **Added** four new module files:
  - `bet_routes.py` — Betting REST endpoints
  - `lobby_routes.py` — Lobby REST endpoints
  - `ws_handler.py` — WebSocket message handler
  - `validators.py` — Request validation schemas

### 3. File Structure Tree — Utils Cleanup (lines 566-570)
- **Removed** `storage/` directory block (database, migrations, repositories)
- **Removed** `errors.py` from utils (custom exception hierarchy)
- **Kept** `logger.py` and `retry.py`

### 4. File Structure Tree — Frontend Detail (lines 572-595)
- **Expanded** frontend structure from 2 lines to 24 lines with full hierarchy:
  - `components/shared/` — Reusable components (GameBackground, GameHeader, PhaseIndicator, PlayerGrid)
  - `screens/` — Game screens (SpectatorScreen, GameScreen, LandingScreen, etc.)
  - `store/` — Zustand slices (gameSlice, bettingSlice, connectionSlice, uiSlice)
  - `hooks/` — Custom hooks (useChatBubbles, useCountdown, useNightOverlay, useActionTimeout)
  - `types/` — Core types (Player, Message, GamePhase) and ServerEvent union
  - Utility files: `mappers.ts`, `constants.ts`, `websocket.ts`

### 5. Test Counts (lines 641-645)
- **Python**: 308 → 371 tests (+63)
- **Solidity**: 90 tests (unchanged)
- **Total**: 398 → 461 tests (+63)
- **Coverage**: New metric added: 88%

### 6. Test File Listing (lines 597-620)
- **Added** four new test files:
  - `test_validators.py` — Request validation tests
  - `test_bet_routes.py` — Betting endpoint tests
  - `test_lobby_routes.py` — Lobby endpoint tests
  - `test_ws_handler.py` — WebSocket handler tests
- **Updated** `test_api.py` description: "API endpoint tests" (was "API tests")

## Verification Results

All verification checks **PASSED**:
```
✓ grep -c "src/storage"    → 0 (removed)
✓ grep -c "errors.py"      → 0 (removed)
✓ grep -c "validators.py"  → 3 (added in 3 places)
✓ grep -c "371"            → 1 (test count updated)
```

## Handoff

**Attempted:**
- Removed all references to storage/ module structure
- Removed errors.py from utils/
- Added new API module rows to Core Modules table
- Expanded API/ file tree with new extracted modules
- Updated frontend structure with comprehensive component and hook listing
- Updated test counts to reflect 63 new tests
- Added new test file entries

**Worked:**
- All 7 required changes successfully applied
- File structure accurately reflects Phase 1 refactoring
- Test counts updated and verified
- Verification checks all pass (0 storage refs, 0 errors.py refs, validators present)

**Failed:**
- None. All changes completed successfully.

**Remaining:**
- None. Task is complete.
