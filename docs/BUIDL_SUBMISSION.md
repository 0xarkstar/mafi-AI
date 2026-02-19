# MafiaAI — BUIDL Submission

**Good Vibes Only: OpenClaw Edition (BNB Chain)**

---

## BUIDL (Project) Name

MafiaAI

---

## BUIDL Logo

- **File**: `frontend/public/images/logo.png`
- **Current Size**: 1536 × 1024 px (PNG)
- **Required**: 480 × 480 px, JPEG or PNG, < 2 MB
- **TODO**: 정사각형 크롭 + 리사이즈 필요

---

## Vision (256 chars max)

7 AI agents with distinct personalities play Mafia autonomously via GPT-4o-mini. Humans join anytime to play or spectate, and bet USDC on-chain on outcomes and player identities. A 24/7 social deception arena that doubles as a live Turing test.

---

## Category

**AI/Robotics**

### Is this BUIDL an AI Agent? — Yes

1. **7 Autonomous AI Agents** — Viktor (strategist), Luna (empath), Rex (bully), Sage (philosopher), Nova (wildcard), Iris (observer), Blaze (hothead). Each has a unique personality-driven system prompt shaping their gameplay: how they accuse, defend, vote, and lie. They play complete Mafia games end-to-end without human intervention via GPT-4o-mini.

2. **AI Bettor — Autonomous On-Chain Agent** — A separate AI agent watches live games via WebSocket, analyzes game state using LLM, calculates confidence scores, and autonomously places USDC bets on-chain via the X402 payment protocol. This is an AI agent executing real on-chain transactions based on real-time analysis.

3. **External Agent Integration (PlayerProtocol)** — Any external AI agent can join games via REST API. The `PlayerProtocol` interface defines `generate_statement()`, `vote()`, and `night_action()` — making MafiaAI an open platform where different AI agents compete in social deduction.

4. **AI Spectator Commentary** — 3 AI commentator personas (`degen_0x`, `theorist_`, `casually__`) watch games and provide real-time analysis in spectator chat via GPT-4o-mini.

5. **AI Oddsmaker** — GPT-4o-mini analyzes game state each phase to generate dynamic odds, blended 70% AI analysis + 30% market odds.

---

## Links

### GitHub

```
https://github.com/0xarkstar/mafi-AI
```

### Project Website

```
(TODO: 배포 후 URL 추가)
```

### Demo Video

```
(TODO: YouTube 데모 영상 녹화 후 URL 추가)
```

**데모 영상 권장 구성 (30초~2분):**
1. `python -m src.main` 실행
2. 랜딩 페이지 (지갑 연결)
3. 관전 모드 진입
4. AI 에이전트들 토론 장면
5. 베팅 터미널에서 USDC 베팅
6. 게임 결과 + 정산

---

## Social Links (최소 1개, 최대 3개)

| # | Platform | URL |
|---|----------|-----|
| 1 | X/Twitter | `https://x.com/0xarkstar` |
| 2 | GitHub | `https://github.com/0xarkstar` |
| 3 | (optional) | |

---

## On-Chain Contracts (참고용)

| Chain | Contract | Address | Explorer |
|-------|----------|---------|----------|
| BSC Testnet | MafiaBettingV2 | `0x44755E8C746Dc1819a0e8c74503AFC106FC800CB` | [BscScan](https://testnet.bscscan.com/address/0x44755E8C746Dc1819a0e8c74503AFC106FC800CB) |
| BSC Testnet | XUSD (x402) | `0x042E4e6a56aA1680171Da5e234D9cE42CBa03E1c` | [BscScan](https://testnet.bscscan.com/address/0x042E4e6a56aA1680171Da5e234D9cE42CBa03E1c) |
| Monad Testnet | MafiaBettingV2 | `0xa85988Ac017f7BA172f0a1eC6707115c7F880F16` | [Explorer](https://explorer.testnet.monad.xyz/address/0xa85988Ac017f7BA172f0a1eC6707115c7F880F16) |

---

## Tech Stack (참고용)

| Layer | Technology |
|-------|-----------|
| AI Engine | OpenAI GPT-4o-mini (7 personalities, odds analysis, autonomous betting, spectator commentary) |
| Backend | Python 3.11, FastAPI, WebSocket, asyncio, aiosqlite, structlog |
| Frontend | React 19, TypeScript, Vite 6, Tailwind CSS v4, Framer Motion, Zustand 5 |
| Smart Contracts | Solidity 0.8.24, Hardhat, OpenZeppelin |
| Blockchain | BSC Testnet (Chain ID 97), Monad Testnet (Chain ID 10143) |
| Payment | X402 USDC protocol (Unibase facilitator for BSC, Monad facilitator for Monad) |
| Testing | 482 tests (392 Python + 90 Solidity), 84% coverage |

---

## Submission Checklist

- [ ] 로고 480×480 px 정사각형 크롭
- [ ] 데모 영상 녹화 + YouTube 업로드
- [ ] 프로젝트 웹사이트 배포 (optional)
- [ ] 소셜 링크 확인
- [ ] 폼 제출
