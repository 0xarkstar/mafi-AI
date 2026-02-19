# mafia-ai Refactoring Plan

## Overview
Code quality improvements across 4 phases: Critical fixes → Backend refactoring → Frontend refactoring → Verification.

## Phase 1: Critical & Security Fixes
- 1.1 AI Bettor immutability (list→tuple) — `src/ai_bettor/client.py`
- 1.2 X402 payment amount extraction — `src/x402/middleware.py`
- 1.3 WebSocket input validation — `src/api/ws_handler.py`
- 1.4 API error handling improvement — `src/api/bet_routes.py`, `lobby_routes.py`
- 1.5 Blockchain gateway amount validation — `src/blockchain/gateway.py`
- 1.6 Test verification after all fixes

## Phase 2: Backend Refactoring
- 2.1 main.py split (entry + cli/terminal.py)
- 2.2 phase_handlers.py split (night, day, vote)
- 2.3 LLM parsing robustness
- 2.4 BettingManager settle logic extraction
- 2.5 Moltbook Agent timeout enforcement
- 2.6 Game engine blockchain error handling
- 2.7 Import pattern unification (TYPE_CHECKING)
- 2.8 Test coverage boost to 90%+

## Phase 3: Frontend Refactoring
- 3.1 SpectatorScreen split (BettingPanel, SpecChatPanel)
- 3.2 GameScreen split (NightOverlay, RoleRevealModal)
- 3.3 WebSocket error logging
- 3.4 Bet input client validation
- 3.5 Error Boundary in App.tsx
- 3.6 Timing constants centralization
- 3.7 XSS protection review

## Phase 4: Verification & Documentation
- 4.1 Full Python test suite + coverage
- 4.2 Frontend build verification
- 4.3 CLAUDE.md update
- 4.4 Commit
