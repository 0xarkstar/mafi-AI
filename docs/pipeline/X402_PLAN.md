# X402 Open Betting Platform — Pipeline Plan

## Phase 1: Implementation (3 sonnet agents, parallel)

| Agent | Module | Creates | Modifies |
|-------|--------|---------|----------|
| p-impl-x402 | `src/x402/` | `__init__.py`, `middleware.py`, `models.py`, `tests/test_x402.py` | `src/config/settings.py`, `pyproject.toml` |
| p-impl-bettor | `src/ai_bettor/` | `__init__.py`, `models.py`, `analyzer.py`, `strategy.py`, `client.py`, `tests/test_ai_bettor.py` | (none) |
| p-impl-api | API integration | `tests/test_x402_betting.py` | `src/api/server.py`, `src/betting/manager.py`, `src/models/betting.py`, `src/main.py` |

**No overlapping files.**

## Phase 2: Verification (1 sonnet agent)

| Agent | Task |
|-------|------|
| p-qa | Full test suite + coverage ≥73%, QA_REPORT.md |

## Done-When

- All existing 154 tests still pass
- New tests pass (~30 new)
- Coverage ≥73%
