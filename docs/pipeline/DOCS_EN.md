# English Documentation Rewrite

**Agent:** p-docs-en
**Task:** Rewrite `docs/USERFLOW.md` and update `README.md` to reflect current codebase state
**Status:** ✅ COMPLETED

---

## Changes Made

### 1. `docs/USERFLOW.md` — Complete Rewrite

**Sections added/updated:**

1. **Running the Game** — Prerequisites (Python 3.11+, Node 18+, OPENAI_API_KEY only), setup steps, 3 run modes (web, CLI, dev)
2. **System Architecture Diagram** — Mermaid diagram showing Backend ↔ WebSocket ↔ Frontend data flow with module responsibility map
3. **Game Lifecycle Flowchart** — Mermaid flowchart: LOBBY → NIGHT → DAY_DISCUSSION → DAY_VOTE → WIN_CHECK → GAME_OVER → REVEAL
4. **Player Interaction Flow** — Sequence diagram for human join/play, ActionPanel UI details
5. **Spectator Flow** — How spectators watch and bet without playing
6. **Betting Flow** — 4 bet types, pari-mutuel calculation, X402 USDC payment protocol with Mermaid sequence diagram
7. **WebSocket Event Map** — Complete list of 15 server→client events and 3 client→server events with data schemas
8. **Screen State Machine** — Mermaid statechart: landing → lobby → game/spectate → reveal → game_over
9. **UI Component Tree** — Updated Mermaid tree with all 37 frontend components
10. **State Management** — 4 Zustand stores (gameStore, chatStore, bettingStore, walletStore) with complete interfaces
11. **Phase Visual Transitions** — Day/night crossfade, phase tints (amber/blue/red/purple), overlay table
12. **Desktop & Mobile Layouts** — 3-column desktop and tabbed mobile descriptions
13. **Optional Features Configuration** — X402, Blockchain, Moltbook, AI Bettor setup
14. **Troubleshooting** — Updated with auto-transition fix note
15. **Performance & Security** — Technical details

### 2. `README.md` — Test Count Update

**Fixed:**
- **Old:** `236 Python + 39 Solidity tests = 275 total`
- **New:** `236 Python + 46 Solidity tests = 282 total` ✅

Updated in both features section and testing section.

---

## Verification Against Source Code

### Enums Verified ✅

From `src/config/constants.py`:
- **Phase**: lobby, night, day_discussion, day_vote, reveal, game_over ✅
- **Role**: mafia, detective, citizen ✅
- **PlayerType**: house_ai, moltbook_agent, agent_human, human ✅
- **BetType**: side_win, next_elimination, is_mafia, is_ai_or_human ✅

### WebSocket Events Verified ✅

From `frontend/src/hooks/useWebSocket.ts`:

**Server → Client (15 events):**
1. phase_change ✅
2. agent_message ✅
3. vote_cast ✅
4. elimination ✅
5. odds_update ✅
6. game_over ✅
7. bet_placed ✅
8. bet_confirmed ✅
9. bet_rejected ✅
10. lobby_joined ✅
11. lobby_status ✅
12. game_starting ✅
13. action_request ✅
14. identity_reveal ✅
15. usdc_settlement ✅
16. pong ✅

**Client → Server (3 events):**
1. join_lobby ✅
2. action_response ✅
3. ping ✅

### Frontend Structure Verified ✅

From `frontend/src/`:
- **Stores**: gameStore, chatStore, bettingStore, walletStore (4) ✅
- **Screens**: landing, lobby, game, spectate, reveal, game_over (6) ✅
- **Component count**: 37 .tsx files in components/ ✅

### Test Counts Verified ✅

From pytest + Hardhat:
- **Python**: 236 tests ✅
- **Solidity**: 46 tests (not 39) ✅
- **Total**: 282 tests ✅

---

## Key Improvements

1. **Auto-transition fix documented** — Added troubleshooting note about fallback in useWebSocket.ts when clients miss game_starting/agent_message events
2. **Accurate WebSocket event data** — All event field names match actual implementation (e.g., `agent` vs `eliminated`, `player_name` vs `name`)
3. **Complete Mermaid diagrams** — System architecture, game lifecycle, screen state machine, UI component tree, betting flow sequence
4. **Module responsibility map** — Clear file ownership and purpose for all src/ and frontend/src/ directories
5. **Zustand store interfaces** — Complete TypeScript interfaces for all 4 stores
6. **Phase visual transitions** — Exact tint colors and special effects per phase
7. **Desktop & Mobile layouts** — ASCII art diagrams showing exact layout structure

---

## Handoff

### What Worked
- Source code analysis of frontend/src/hooks/useWebSocket.ts provided exact event list
- Reading constants.py confirmed all enums
- Reading gameStore.ts confirmed store structure
- pytest --collect-only gave accurate Python test count
- Grep on Solidity test file gave accurate test count

### What Didn't Work
- Initial grep for Solidity tests returned 0 (searched for `test(` instead of `it(`)

### Remaining Work
- **Task #4**: Translate docs/USERFLOW.md → docs/USERFLOW.ko.md (Korean translation)
- **Task #4**: Update README.ko.md with corrected test counts (if Korean README exists)

---

**Files Modified:**
- ✅ `docs/USERFLOW.md` (1106 lines, complete rewrite)
- ✅ `README.md` (2 edits: test count 275→282)
- ✅ `docs/pipeline/DOCS_EN.md` (this file)

**No code files modified** — documentation-only changes as required.
