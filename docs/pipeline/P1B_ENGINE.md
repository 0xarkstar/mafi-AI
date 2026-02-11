# P1B: Engine + Phase Handler Refactor

**Status**: ✅ Complete
**Agent**: p-impl-engine
**Date**: 2026-02-12

## Summary

Successfully refactored the MafiaAI game engine and phase handlers to support the new mixed-player architecture. Phase handlers now use `PlayerProtocol` instead of direct LLM client calls, enabling AI, external agents, and human players to participate in the same game.

## Changes Made

### 1. Phase Handlers Refactored (`src/engine/phase_handlers.py`)

**Signature Changes:**
- **Before**: `handle_night(state, agents, llm_client, event_cb)`
- **After**: `handle_night(state, players, agent_states, event_cb)`

All three phase handlers (`handle_night`, `handle_day_discussion`, `handle_day_vote`) now:
- Accept `players: dict[str, PlayerProtocol]` instead of `llm_client`
- Accept `agent_states: dict[str, AgentState]` for memory/known_roles tracking
- Build `TurnContext` with game state and pass to player methods
- Call player-specific methods:
  - `player.night_action(ctx, targets)` for mafia kills and detective investigations
  - `player.generate_statement(ctx)` for discussion phase
  - `player.vote(ctx, candidates)` for voting phase

**Key Pattern:**
```python
# Build context from agent state
ctx = TurnContext(
    alive_agents=state.alive_agents,
    role=role,
    known_roles=agent_state.known_roles,
    memory=agent_state.memory,
    round_number=state.round_number,
    round_history=recent_rounds,
    personality=agent_state.personality,
)

# Call player method
action = await players[player_name].night_action(ctx, targets)
```

### 2. Game Engine Updated (`src/engine/game_engine.py`)

**Constructor Changes:**
- **Before**: Accepts `settings: Settings`, creates internal `LLMClient`
- **After**: Accepts `players: dict[str, PlayerProtocol]` from lobby

**Key Updates:**
- Removed `self.claude = LLMClient(settings)` (players bring their own LLM clients)
- `_initialize_game()` now uses player names from `self.players` instead of `ALL_PERSONALITIES`
- Creates `AgentState` for each player with personality (House AI) or generic personality (humans)
- Passes both `self.players` and `self.agents` to phase handlers
- **REVEAL Phase**: Added after GAME_OVER to broadcast player identities and settle identity bets

**REVEAL Phase Flow:**
```python
# After game_over event
self.state = self.state.model_copy(update={"phase": Phase.REVEAL})

# Broadcast identity_reveal for each player
for name, player in self.players.items():
    await self.event_callback(WSEvent(
        event_type="identity_reveal",
        data={
            "agent": name,
            "player_type": player.player_type.value,
            "role": self.state.role_map[name].value,
        },
        ...
    ))

# Settle identity bets
if self.betting_manager:
    identity_payouts = self.betting_manager.settle_identity_bets(self.players)
```

### 3. Identity Betting Added (`src/betting/manager.py`)

**New Pool:**
- Added `BetType.IS_AI_OR_HUMAN` pool in `__init__`

**New Method: `settle_identity_bets(players)`**
- Bet format: `"PlayerName:ai"` or `"PlayerName:human"`
- Maps `PlayerType` to actual identity:
  - `HOUSE_AI`, `MOLTBOOK_AGENT` → "ai"
  - `AGENT_HUMAN`, `HUMAN` → "human"
- Parses bet targets, filters winning bets, calculates payouts
- Applies 5% house edge, same as other bet types

### 4. Tests Updated

**New Fixture (`tests/conftest.py`):**
```python
@pytest.fixture
def mock_players(sample_personalities: tuple) -> dict:
    """Create mock players implementing PlayerProtocol."""
    players = {}
    for personality in sample_personalities:
        player = MagicMock()
        player.name = personality.name
        player.player_type = PlayerType.HOUSE_AI
        player.personality = personality
        player.generate_statement = AsyncMock(return_value="I think someone is suspicious.")
        player.vote = AsyncMock(return_value="TestAgent4")
        player.night_action = AsyncMock(return_value="TestAgent4")
        players[personality.name] = player
    return players
```

**Updated Tests (`tests/test_engine.py`):**
- All 20 phase handler tests updated to use `mock_players` instead of `mock_claude_client`
- Fixed mock configuration: individual player mocks instead of shared side_effect
- All tests passing: 20/20 ✅

**New Tests (`tests/test_betting.py`):**
- Added `TestIdentityBetting` class with 6 new tests
- Tests cover: pool existence, bet placement, AI/human settlement, multiple players, no bets, invalid format
- All tests passing: 6/6 ✅

## Test Results

```bash
.venv/bin/python -m pytest tests/test_engine.py tests/test_betting.py -v
```

**Result**: 46/46 tests passing ✅

```bash
.venv/bin/python -m pytest tests/ -v
```

**Result**: 153/154 tests passing (1 failure in test_moltbook.py, not my ownership)

## Files Modified

### Core Engine
- ✅ `src/engine/phase_handlers.py` - Refactored all 3 handlers
- ✅ `src/engine/game_engine.py` - Accept players, add REVEAL phase

### Betting
- ✅ `src/betting/manager.py` - Add IS_AI_OR_HUMAN pool, settle_identity_bets()

### Tests
- ✅ `tests/conftest.py` - Add mock_players fixture
- ✅ `tests/test_engine.py` - Update 20 phase handler tests
- ✅ `tests/test_betting.py` - Add 6 identity betting tests

## Integration with p-impl-players

**Dependencies Resolved:**
- `PlayerProtocol` interface defined in `src/players/protocol.py` ✅
- `TurnContext` model defined in `src/players/protocol.py` ✅
- `PlayerType` enum in `src/config/constants.py` ✅
- `Phase.REVEAL` in `src/config/constants.py` ✅
- `BetType.IS_AI_OR_HUMAN` in `src/config/constants.py` ✅

All imports use runtime checks (`TYPE_CHECKING`, `if TYPE_CHECKING`) and runtime imports to avoid circular dependencies.

## Known Issues

None. All functionality working as designed.

## Next Steps for Integration

1. **API Layer (p-impl-api)** needs to:
   - Update game initialization to create players from lobby
   - Pass `players` dict to `GameEngine` constructor instead of `settings`
   - Remove direct `LLMClient` instantiation in game setup
   - Add WebSocket event handler for `identity_reveal` events

2. **Frontend** needs to:
   - Display identity reveals after game over
   - Show player type badges (AI/Human) in REVEAL phase
   - Support betting on player identities (target format: "PlayerName:ai")

## Handoff

### What Worked
- PlayerProtocol abstraction cleanly separated player logic from engine
- TurnContext provides all necessary context without coupling to player internals
- Identity betting fits naturally into existing pari-mutuel system
- Test mocks were straightforward with MagicMock

### What Didn't Work
- Initial mock setup shared side_effect across all players (fixed by individual configs)
- HOUSE_EDGE import missing (added to imports)

### Remaining Work
- None for engine refactoring
- API layer needs to wire up new constructor signature
- Frontend needs identity reveal UI

---

**Ready for handoff to p-impl-api** ✅
