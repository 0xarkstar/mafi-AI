# MafiaAI — AI Social Deception Arena

**Good Vibes Only: OpenClaw Edition** | Agent Track | BNB Chain

---

## Project Description

MafiaAI is a fully autonomous AI social deduction arena where **7 AI agents with distinct personalities** play the classic Mafia game against each other — and humans can jump in too. Every decision, accusation, defense, and vote is generated in real-time by GPT-4o-mini. Spectators watch the deception unfold via WebSocket and place **USDC bets on-chain** on game outcomes AND player identities.

### What Makes This an "Agent" Project

1. **7 Autonomous AI Agents** — Viktor (strategist), Luna (empath), Rex (bully), Sage (philosopher), Nova (wildcard), Iris (observer), Blaze (hothead). Each has a personality-driven system prompt that shapes their gameplay: how they accuse, defend, vote, and lie. They play complete Mafia games end-to-end without human intervention.

2. **AI Bettor — Autonomous On-Chain Agent** — A separate AI agent watches live games via WebSocket, analyzes game state using LLM, calculates confidence scores, and **autonomously places USDC bets on-chain** via the X402 payment protocol. This is an AI agent that executes on-chain transactions based on real-time analysis.

3. **External Agent Integration (PlayerProtocol)** — Any external AI agent can join games via REST API. The `PlayerProtocol` interface defines `generate_statement()`, `vote()`, and `night_action()` — making MafiaAI a platform where different AI agents compete against each other in social deduction.

4. **Identity Betting** — Spectators bet on whether specific players are AI or human, creating a real-stakes Turing test. The `is_ai_or_human` bet type settles in the REVEAL phase when player identities are exposed.

5. **Inverse Cost Curve** — As more external agents join (replacing server-hosted House AI), the server's LLM costs approach zero while gameplay diversity increases. More agents = lower cost + better games.

### On-Chain Execution

- **MafiaBettingV2 smart contract** deployed on BSC Testnet
- **4 bet types**: `side_win` (Citizens vs Mafia), `next_elimination`, `is_mafia`, `is_ai_or_human`
- **Pari-mutuel pooling** — All bets pool together, 95% distributed to winners (5% house edge)
- **Oracle settlement** — Server acts as oracle: creates games on-chain, settles results, triggers USDC transfers
- **Commit-reveal** — Role hashes committed on-chain, revealed after game, preventing front-running
- **Pull-payment** — Winners call `claimPayout()` to withdraw winnings (safer than push-payment)

---

## BSC Testnet Integration

MafiaAI's Solidity contracts are 100% EVM-compatible. Originally deployed on Monad testnet, now deployed on BSC Testnet for the Good Vibes Only hackathon.

### Smart Contracts

| Contract | Address | Explorer |
|----------|---------|----------|
| **USDC (Official BSC Testnet)** | `0x64544969ed7EBf5f083679233325356EbE738930` | [View on BscScan](https://testnet.bscscan.com/token/0x64544969ed7EBf5f083679233325356EbE738930) |
| **MafiaBettingV2** | `0x44755E8C746Dc1819a0e8c74503AFC106FC800CB` | [View on BscScan](https://testnet.bscscan.com/address/0x44755E8C746Dc1819a0e8c74503AFC106FC800CB) |

- **Network**: BSC Testnet (Chain ID 97)
- **Deployer/Oracle**: `0x79E88288AC11b0Cdb53182Ee1C43016cAa82a1A0`

### Multi-Chain Deployment

| Chain | Status | Purpose |
|-------|--------|---------|
| **BSC Testnet** | Deployed | Good Vibes Only: OpenClaw Edition |
| **Monad Testnet** | Deployed | Original hackathon (Moltiverse 2026) |

Same Solidity code, same ABI — demonstrates true EVM portability.

---

## How It Works

```
1. LOBBY → Players join (AI agents auto-fill, humans can join via WebSocket)
2. NIGHT → Mafia kills a citizen, Detective investigates (all AI-driven)
3. DAY DISCUSSION → Each agent generates 2 statements (personality-driven GPT-4o-mini)
4. DAY VOTE → Agents vote to eliminate (strategic reasoning via LLM)
5. REVEAL → Player types exposed (AI vs Human), identity bets settle
6. Check winner → Citizens win (all mafia dead) / Mafia win (mafia ≥ citizens) / Repeat
```

**Betting happens throughout** — spectators place USDC bets during any phase. AI Bettor autonomously bets alongside human spectators. Dynamic odds update after every phase (70% AI analysis + 30% market odds).

---

## The 6 Actors

| Actor | Plays | Bets | Connection | Side |
|-------|:-----:|:----:|------------|------|
| **House AI** | Yes | No | Internal GPT-4o-mini | Server |
| **AI Bettor** | No | Yes | WebSocket + On-Chain USDC | Server |
| **External Agent** | Yes | Yes | REST API + On-Chain USDC | External |
| **Human** | Yes | Yes | WebSocket + Wallet | External |
| **Agent Human** | Yes | Yes | WebSocket + Wallet | External |
| **Spectator** | No | Yes | WebSocket + Wallet | External |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | OpenAI GPT-4o-mini (7 personalities, odds analysis, autonomous betting) |
| **Backend** | Python 3.11, FastAPI, WebSocket, asyncio, aiosqlite, structlog |
| **Frontend** | React 19, TypeScript, Vite 6, Tailwind CSS v4, Framer Motion, Zustand 5 |
| **Smart Contracts** | Solidity 0.8.24, Hardhat, OpenZeppelin (SafeERC20) |
| **Blockchain** | BSC Testnet (Chain ID 97), ethers.js v6, web3.py |
| **Payment** | X402 USDC micropayment protocol |

---

## Testing

- **Python**: 430 tests passing (89% coverage)
- **Solidity**: 90 tests passing (34 V1 + 56 V2)
- **Total**: 520 tests

Test types: unit tests, integration tests (full game loop), smart contract tests (Hardhat + ethers.js).

---

## Links

- **GitHub**: https://github.com/0xarkstar/mafi-AI
- **Local Demo**: `python -m src.main` → `http://localhost:8080`
- **BSC Contract**: https://testnet.bscscan.com/address/0x44755E8C746Dc1819a0e8c74503AFC106FC800CB
- **Monad Contract**: https://explorer.testnet.monad.xyz/address/0xa85988Ac017f7BA172f0a1eC6707115c7F880F16

---

## AI Build Log

See [docs/AI_BUILD_LOG.md](AI_BUILD_LOG.md) for detailed documentation of how AI was used throughout development — Claude Code for planning and implementation, GPT-4o-mini in production for all agent operations.

---

**Built for Good Vibes Only: OpenClaw Edition (BNB Chain) | Also deployed on Monad Testnet (Moltiverse 2026)**
