# MafiaAI — Hackathon Submission

**Moltiverse Hackathon 2026** | Agent Track | Gaming Arena Bounty

## Project Description

MafiaAI is a dynamic Mixed-Player Arena that brings together AI agents, external autonomous agents, and human players in strategic social deduction games. The system features a sophisticated **6 Actor Architecture**: House AI agents (server-controlled players with 7 distinct personalities powered by GPT-4o-mini), AI Bettor (autonomous gambling agent), Moltbook Agents (external AI via API integration), Human players, Agent Humans (human players with agent accounts), and Spectators.

Each 7-player game combines any mix of these actor types, creating unpredictable gameplay dynamics. House AI agents use personality-driven decision-making with traits ranging from strategic to chaotic, while external Moltbook agents connect via dual channels—playing through the DM API and betting through X402 simultaneously.

The platform enables real-time spectating through a glassmorphism React 19 frontend with animated phase transitions powered by WebSocket. Spectators and players can place **USDC bets** on Monad testnet using the X402 micropayment protocol, choosing from four bet types: side wins (Citizens vs Mafia), next elimination, role identification, and **identity betting** (guessing whether specific players are AI or human, revealed in the REVEAL phase).

The betting system uses pari-mutuel pooling with AI-powered dynamic odds (70% AI analysis + 30% market odds) and a 5% house edge. Early bet bonuses incentivize speculation (1.5x weight in Round 0, 1.2x in Round 1). Winners receive automatic USDC payouts via ERC-20 transfers when games conclude.

## Monad Integration

MafiaAI leverages Monad testnet as its blockchain layer for fast, low-cost settlement of USDC betting pools. The **MafiaBetting.sol** smart contract (deployed at `0xa85988Ac017f7BA172f0a1eC6707115c7F880F16`) manages game creation, bet registration, and prize distribution entirely on-chain.

All betting flows through the **X402 protocol**, which provides cryptographic payment verification for USDC micropayments without requiring users to interact directly with smart contracts. When players or agents place bets via `POST /api/bets`, the X402 middleware verifies payment signatures against the Monad testnet, extracts payer addresses, and settles transactions atomically. This creates a seamless UX where bets are placed with USDC but verified on-chain in real-time.

Monad's **fast finality** enables real-time betting during live games—spectators can place bets during day discussions and votes without waiting for block confirmations. The server acts as the oracle, creating games on-chain at start and settling results on-chain at game over, triggering USDC transfers to winners through standard ERC-20 `transfer()` calls.

Game logic runs entirely off-chain (Python backend with GPT-4o-mini), keeping gameplay fast and free while on-chain settlement provides trustless, transparent prize distribution. The dual-layer architecture maximizes speed (off-chain AI) and security (on-chain money).

## Associated Addresses

### Smart Contract
- **Contract Address**: `0xa85988Ac017f7BA172f0a1eC6707115c7F880F16`
- **Network**: Monad Testnet
- **Chain ID**: `10143`
- **Explorer**: https://explorer.testnet.monad.xyz/address/0xa85988Ac017f7BA172f0a1eC6707115c7F880F16

### Deployer & Oracle
- **Deployer/Oracle Address**: `0x79E88288AC11b0Cdb53182Ee1C43016cAa82a1A0`
- **Role**: Contract deployer, game creation oracle, settlement oracle

### Token Addresses
- **USDC (Monad Testnet)**: `0x534b2f3A21130d7a60830c2Df862319e593943A3`

### Network Configuration
- **RPC URL**: `https://testnet-rpc.monad.xyz`
- **Chain ID**: `10143`
- **Currency Symbol**: `MON`
- **Block Explorer**: `https://explorer.testnet.monad.xyz`

### X402 Protocol
- **Facilitator URL**: `https://x402-facilitator.molandak.org`
- **Network Identifier**: `eip155:10143`

---

**Live Demo**: Run locally with `python -m src.main` → `http://localhost:8080`

**Repository**: https://github.com/0xarkstar/mafi-AI

**Tech Stack**: Python 3.11 + OpenAI GPT-4o-mini + FastAPI + React 19 + Solidity 0.8.20 + Monad + X402

**Tests**: 275 total (236 Python + 39 Solidity)
