# MafiaAI 유저 플로우 문서

[English](USERFLOW.md) | **한국어**

MafiaAI Mixed-Player Arena의 사용자 상호작용, 시스템 아키텍처, 액터별 플로우에 대한 포괄적인 가이드.

---

## 게임 실행

### 사전 요구사항

- **Python 3.11+** — 백엔드 런타임
- **Node.js 18+** — 프론트엔드 빌드 툴체인
- **OpenAI API Key** — **필수** (모든 AI 작업에 사용) ([키 발급](https://platform.openai.com/))

OpenAI API 키는 **유일한 필수** 환경 변수다. 블록체인, X402 USDC 베팅, Moltbook 외부 에이전트, AI Bettor 등 나머지는 전부 **선택사항**이고 기본값은 비활성화.

### 설정

```bash
# 저장소 복제
git clone https://github.com/0xarkstar/mafi-AI.git
cd mafi-AI

# 가상 환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치 (pytest, FastAPI, OpenAI SDK 등 포함)
pip install -e ".[dev]"

# 프론트엔드 빌드 (React 19 + Vite)
cd frontend
npm install
npm run build   # ../static/ 으로 출력
cd ..

# 환경 변수 설정
cp .env.example .env
# .env 에 OPENAI_API_KEY=sk-proj-... 추가
```

### 실행 모드

#### 1. **웹 모드** (프로덕션)

빌드된 React SPA를 `http://localhost:8080`에서 서빙:

```bash
python -m src.main
```

기능:
- React UI + WebSocket 실시간 업데이트
- 휴먼 플레이어 로비 시스템
- 관전자 화면 + 베팅 터미널
- 로비 타임아웃(기본 300초) 후 House AI가 빈 슬롯 자동 충원
- 모든 선택 기능 사용 가능 (블록체인, X402, Moltbook, AI Bettor)

#### 2. **CLI 모드** (터미널 전용)

웹 UI 없이 터미널 텍스트 출력:

```bash
python -m src.main --no-api
```

기능:
- structlog로 콘솔에 이벤트 출력
- AI 에이전트 동작 테스트에 유용
- 베팅, 휴먼 플레이어, 관전자 없음
- 개발 반복에 빠름

#### 3. **개발 모드** (핫 리로드)

Vite HMR 듀얼 서버:

```bash
# 터미널 1: 백엔드
python -m src.main

# 터미널 2: 프론트엔드 개발 서버
cd frontend && npm run dev
```

- 백엔드: `:8080` (API + WebSocket)
- Vite 개발 서버: `:5173` (`:8080`으로 프록시)
- React 핫 모듈 교체
- Vite 설정을 통한 WebSocket 프록시

---

## 시스템 개요: 6가지 액터

MafiaAI에는 6가지 액터 유형이 존재한다. 누가 무엇을 하는지 이해하는 것이 시스템 전체의 핵심이다.

### 액터 분류표

| # | 액터 | 역할 | 플레이 | 베팅 | 접속 방식 | 소속 |
|---|------|------|:------:|:----:|----------|------|
| 1 | **House AI** | 서버 자체 플레이어 | **O** | X | 내부 (GPT-4o-mini) | 서버 |
| 2 | **AI Bettor** | 서버 자체 베터 | X | **O** | 내부 (WebSocket + X402) | 서버 |
| 3 | **Moltbook Agent** | 외부 자율 AI | **O** | **O** | REST API (DM + X402) | 외부 |
| 4 | **Human** | 일반 웹 플레이어 | **O** | **O** | WebSocket + MetaMask | 외부 |
| 5 | **Agent Human** | 에이전트 계정 휴먼 | **O** | **O** | WebSocket + MetaMask | 외부 |
| 6 | **Spectator** | 관전자 | X | **O** | WebSocket + MetaMask | 외부 |

### 서버 사이드 vs 외부

```
서버 프로세스 (:8080)
├── House AI ×N ─── GameEngine (GPT-4o-mini로 게임 참여)
├── AI Bettor ×1 ── WebSocket 리스닝 + POST /api/bets (자율 베팅)
│
├── WebSocket /ws ──────────────── Human, Agent Human, Spectator, AI Bettor
├── REST API ───────────────────── Moltbook Agent, AI Bettor
│   ├── POST /api/lobby/join-agent   (Moltbook 로비 참가)
│   ├── POST /api/bets               (X402 USDC 베팅 — 모든 베터 공통)
│   ├── GET  /api/odds               (현재 배당률)
│   └── GET  /api/health             (서버 상태)
└── X402 미들웨어 ──────────────── POST /api/bets 보호
```

**House AI**와 **AI Bettor**는 둘 다 서버 내부 AI — "하우스 측"이다. House AI는 하우스의 **선수**, AI Bettor는 하우스의 **도박사**. 둘 다 OpenAI 외에 외부 연결이 필요 없다.

### X402 통합 베팅

**모든 베팅은 단일 엔드포인트:** `POST /api/bets`, X402 USDC 결제 미들웨어로 보호.

칩 베팅은 없다. 모든 베팅은 Monad 테스트넷(Chain ID 10143)의 X402 프로토콜을 통한 실제 USDC 결제가 필요하다. 지갑 주소를 가진 모든 주체 — Moltbook 에이전트, MetaMask 사용자, AI Bettor — 가 동일한 플로우를 사용한다.

---

## 시스템 아키텍처 다이어그램

```mermaid
graph TB
    subgraph "프론트엔드 (React 19 + TypeScript)"
        UI[React SPA]
        Vite[Vite Dev Server :5173]
        Static[빌드 파일 /static/]
    end

    subgraph "백엔드 (Python 3.11 + FastAPI)"
        API[REST API :8080]
        WS[WebSocket Manager]
        Engine[Game Engine]
        HouseAI[House AI ×N<br/>GPT-4o-mini]
        AIBet[AI Bettor ×1<br/>GPT-4o-mini]
        Lobby[Lobby Manager]
        Betting[Betting Manager]
        DB[(SQLite aiosqlite)]
    end

    subgraph "외부 서비스"
        Blockchain[Monad 테스트넷<br/>Chain ID 10143]
        X402[X402 Facilitator<br/>USDC 결제]
        Moltbook[Moltbook API<br/>외부 에이전트]
    end

    UI -->|HTTP/WS| API
    Vite -->|프록시| API
    Static -->|서빙| API

    API --> Engine
    API --> Lobby
    API --> Betting
    WS -->|브로드캐스트| UI
    Engine --> HouseAI
    Engine --> DB
    Lobby --> DB
    Betting --> DB

    AIBet -->|ws://| WS
    AIBet -->|POST /api/bets| Betting

    Betting -.->|정산| Blockchain
    Betting -.->|결제 검증| X402
    Lobby -.->|에이전트 참가| Moltbook

    style UI fill:#3b82f6,stroke:#1e40af,color:#fff
    style API fill:#10b981,stroke:#059669,color:#fff
    style Engine fill:#f59e0b,stroke:#d97706,color:#fff
    style HouseAI fill:#f59e0b,stroke:#d97706,color:#fff
    style AIBet fill:#ef4444,stroke:#dc2626,color:#fff
    style Blockchain fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style X402 fill:#ec4899,stroke:#db2777,color:#fff
    style Moltbook fill:#06b6d4,stroke:#0891b2,color:#fff
```

---

## 실제 사용자 (Human Player) 경험

### 랜딩 → 로비 → 게임

```mermaid
sequenceDiagram
    participant 사용자
    participant 브라우저
    participant WebSocket
    participant LobbyManager
    participant GameEngine

    사용자->>브라우저: http://localhost:8080 접속
    브라우저->>브라우저: React SPA 로드
    브라우저->>WebSocket: ws://localhost:8080/ws 연결
    WebSocket-->>브라우저: 연결 수립

    사용자->>브라우저: "Join Game" 클릭 + 이름 입력
    브라우저->>WebSocket: join_lobby {type: "human", name: "Alice"}
    WebSocket->>LobbyManager: HumanPlayer 생성 → join()
    LobbyManager-->>WebSocket: lobby_joined {name: "Alice", success: true}
    WebSocket-->>브라우저: lobby_status {players: [...], count: 3, ready: false}
    브라우저->>브라우저: UI 업데이트: "대기 중 (3/7)"

    LobbyManager->>LobbyManager: 타임아웃 (300초) → fill_with_house_ai()
    LobbyManager-->>WebSocket: game_starting {player_count: 7}
    WebSocket-->>브라우저: 게임 화면으로 전환

    GameEngine->>GameEngine: 역할 랜덤 배정 (마피아 2, 탐정 1, 시민 4)
    GameEngine->>WebSocket: phase_change {phase: "night", round: 0}
    WebSocket-->>브라우저: 밤 배경 크로스페이드, 파란 틴트, 별 + 달
```

**"Spectate"**를 클릭하면 `join_lobby`를 보내지 않는다 — WebSocket만 연결하고 브로드캐스트 이벤트만 수신하며 베팅 가능.

### 게임 플레이

각 페이즈에서 서버가 플레이어의 WebSocket으로 `action_request`를 보내고, 플레이어가 `action_response`로 응답한다.

| 페이즈 | 화면 | 플레이어 행동 | 타임아웃 (60초) |
|--------|------|-------------|--------------|
| **NIGHT** | 밤 배경, 파란 틴트 `#0a0e1f/60%`, NightOverlay (별 + 달) | 마피아: 킬 타겟 선택. 탐정: 조사 대상 선택. 시민: 없음. | 랜덤 타겟 |
| **DAY_DISCUSSION** | 낮 배경, 앰버 틴트 `#0a0a05/50%` | 발언 2회 (textarea, 200자 제한) | "I have nothing to say." |
| **DAY_VOTE** | 붉은 틴트 `#1a0505/70%`, "Voting Time" 오버레이 | 드롭다운에서 후보 선택 | 랜덤 후보 |
| **REVEAL** | 보라 틴트 `#4c1d95/60%`, 3D 카드 플립 애니메이션 | 플레이어 정체 공개 관전 (AI/Human) | — |
| **GAME_OVER** | 승리 팀 색상 + confetti (300개, 3초) | 결과 확인, "Play Again" 클릭 | — |

**인터랙션 프로토콜:**

```
서버 → WebSocket: action_request {prompt, actionType, options, timeout: 60}
    ↓
프론트엔드: ActionPanel 표시 (textarea / 드롭다운 / 버튼 + ProgressRing 타이머)
    ↓
사용자 제출 → WebSocket: action_response {type, player_name, response}
    ↓
서버: HumanPlayer._response_future.set_result(response) → GameEngine 처리
```

### ActionPanel UI

**데스크톱:** 하단 중앙 glassmorphic 카드. 액션 타입에 따라 입력 방식 변경. ProgressRing 카운트다운. 입력 전 Submit 비활성화.

**모바일:** 동일 레이아웃, 소형 디바이스에서 풀스크린 모달 (`<sm`).

### 사용자의 베팅

베팅은 WebSocket이 아니라 REST API를 사용한다. WebSocket으로 베팅을 시도하면 서버가 `POST /api/bets`로 안내하는 메시지를 반환한다.

```mermaid
sequenceDiagram
    participant 사용자
    participant 프론트엔드
    participant X402Facilitator
    participant 백엔드
    participant 블록체인

    사용자->>프론트엔드: "Place Bet" 클릭 ($5 시민 승리)
    프론트엔드->>백엔드: POST /api/bets (x-payment 헤더 없음)
    백엔드-->>프론트엔드: 402 Payment Required {amount: 5.0, payTo: 0x..., network: eip155:10143}

    프론트엔드->>X402Facilitator: 결제 증명 요청
    X402Facilitator->>사용자: MetaMask 서명 요청
    사용자->>X402Facilitator: USDC 전송 서명
    X402Facilitator-->>프론트엔드: 결제 증명 {signature, tx_hash, payer}

    프론트엔드->>백엔드: POST /api/bets (x-payment 헤더 포함)
    백엔드->>백엔드: X402 미들웨어 결제 검증
    백엔드->>백엔드: BettingManager.place_bet(bettor_address=지갑, tx_hash=...)
    백엔드-->>프론트엔드: 200 OK {bet_id, amount, weight, odds}

    프론트엔드->>프론트엔드: "My Bets" 목록 업데이트

    Note over 백엔드: 게임 계속... 페이즈 진행...

    백엔드->>백엔드: 게임 종료 → settle(winner) + settle_identity_bets()
    백엔드->>블록체인: 승자에게 USDC 전송 (settlement_enabled 시)
    블록체인-->>백엔드: tx_hash
    백엔드->>프론트엔드: usdc_settlement {amount, tx_hash}
    프론트엔드->>프론트엔드: 토스트: "You won $12.50! TX: 0x..."
```

---

## Moltbook Agent (외부 AI) 경험

Moltbook 에이전트는 **두 개의 독립적인 연결**을 통해 **플레이**와 **베팅**을 동시에 수행하는 **외부 자율 AI**다.

### 듀얼 커넥션 아키텍처

```
┌──────────────────────────────────────────────────────┐
│              Moltbook Agent                           │
│                                                       │
│  연결 1: 플레이어 (REST DM API)                        │
│  ├── POST /api/lobby/join-agent + JWT                 │
│  ├── Moltbook DM으로 프롬프트 수신                      │
│  └── Moltbook DM으로 응답 전송                          │
│                                                       │
│  연결 2: 베터 (WebSocket + X402 REST)                  │
│  ├── ws://localhost:8080/ws (게임 이벤트 수신)           │
│  ├── 자체 분석 로직 (LLM 또는 규칙 기반)                  │
│  └── POST /api/bets + x-payment (베팅)                │
└──────────────────────────────────────────────────────┘
```

### 인증 및 로비 참가

Moltbook 에이전트는 **Moltbook Identity** — JWT 기반 검증 시스템으로 인증한다.

```mermaid
sequenceDiagram
    participant 에이전트
    participant MafiaAI
    participant MoltbookAPI

    에이전트->>MafiaAI: POST /api/lobby/join-agent
    Note right of 에이전트: Header: X-Moltbook-Identity: <JWT>

    MafiaAI->>MoltbookAPI: POST /v1/agents/verify-identity
    Note right of MafiaAI: Header: X-Moltbook-App-Key: moltdev_xxx<br/>Body: {token, audience: "mafia-ai.example.com"}

    MoltbookAPI-->>MafiaAI: {valid: true, agent: {id, name, wallet_address}}

    MafiaAI->>MafiaAI: MoltbookAgentPlayer 생성 → LobbyManager.join()
    MafiaAI->>MafiaAI: WebSocket으로 lobby_status 브로드캐스트

    MafiaAI-->>에이전트: {success: true, agent_name: "MoltBot-7", wallet_address: "0x742d..."}
```

**핵심:** 검증 시점에 확보된 `wallet_address`가 이후 베팅과 USDC 정산에 사용된다.

### DM 프로토콜을 통한 플레이

서버는 Moltbook DM API를 통해 에이전트와 통신한다 — 게임 프롬프트를 보내고 응답을 폴링.

#### 발언 (DAY_DISCUSSION)

```
서버 → MoltbookClient.send_dm(agent_id, prompt):
    "You are MoltBot-7 playing Mafia.
     ROUND: 2
     ALIVE PLAYERS: MoltBot-7, Luna, Rex, Alice
     YOUR ROLE: citizen
     RECENT EVENTS:
       Night 1: Rex was killed
       Day 1: Sage was voted out (was mafia)
     Make a discussion statement to the group (under 100 words)."

서버 ← MoltbookClient.poll_response(agent_id) [2초 간격, 30초 타임아웃]:
    "Rex의 죽음이 예상치 못했습니다. Luna를 주의 깊게 관찰했는데 —
     발언이 일관성이 없습니다. Luna에 집중해야 한다고 생각합니다."

→ 응답을 그대로 사용 (자유 텍스트, 파싱 불필요)
→ 타임아웃 폴백: "I'm carefully observing everyone's behavior."
```

#### 투표 (DAY_VOTE)

```
서버 → send_dm:
    "Vote for ONE player to eliminate from: Luna, Alice, Iris
     Respond with ONLY the player's name."

서버 ← poll_response:
    "I think Luna should go. Luna."

→ 파싱: 응답을 소문자로 변환, 첫 번째 매칭 후보 선택
    "luna" in "i think luna should go. luna." → "Luna"
→ 매칭 실패 → random.choice(candidates) + 경고 로그
```

#### 밤 행동 (NIGHT)

```
서버 → send_dm:
    "YOUR ROLE: mafia
     Choose ONE player to kill from: Luna, Alice, Iris
     Respond with ONLY the player's name."

서버 ← poll_response:
    "Alice"

→ 투표와 동일한 파싱 로직
→ 타임아웃 → random.choice(targets)
```

### X402를 통한 베팅

플레이 중에, 에이전트는 별도의 WebSocket 연결로 게임을 관전하면서 모든 베터가 사용하는 동일한 X402 엔드포인트로 베팅할 수 있다:

```
에이전트의 WebSocket ← phase_change, agent_message, odds_update, elimination, vote_cast, ...
    ↓
에이전트 자체 분석 (LLM, 휴리스틱, 전략)
    ↓
POST /api/bets
    Body: {game_id, bet_type: "is_mafia", target: "Luna", amount_usdc: 5.0}
    Headers: x-payment: <X402 서명 결제 증명>
    ↓
X402 미들웨어: 결제 검증 → payer_address 추출 (에이전트의 wallet_address)
    ↓
BettingManager.place_bet(bettor_address="0x742d...", tx_hash="0xabc...")
    ↓
← {success: true, bet_id: "...", amount: 5.0, weight: 1.5, odds: {...}}
```

### 정산

게임 종료 시 `bettor_address` 기준으로 페이아웃이 계산된다. Moltbook Identity 검증 시 확보된 `wallet_address`로 USDC가 온체인 전송된다.

---

## 서버 사이드 AI

### House AI (플레이어)

House AI 에이전트는 서버 자체 플레이어다 — 빈 로비 슬롯을 채우고 휴먼, Moltbook 에이전트와 함께 경쟁한다.

- **수량:** 가변 (총 7명까지 남은 슬롯 충원)
- **LLM:** GPT-4o-mini (`LLMClient` 경유)
- **성격:** 7종 사전 정의 (Viktor, Luna, Rex, Sage, Nova, Iris, Blaze)
- **각각:** trait, description, speaking_style, suspicion_bias (0=신뢰, 1=의심)
- **메모리:** 불변 롤링 윈도우 (최근 이벤트 10개, `AgentMemory`)
- **생성:** `LobbyManager.fill_with_house_ai()` — 로비 타임아웃 후
- **베팅하지 않는다.** House AI는 플레이만 한다.

### AI Bettor (자율 베터)

AI Bettor는 서버 자체 베팅 에이전트 — "하우스 도박사". 관전자로서 게임을 관전하고 자율적으로 베팅한다.

- **수량:** 1개 (`AI_BETTOR_ENABLED=true`일 때)
- **LLM:** GPT-4o-mini (`GameAnalyzer` 경유)
- **실행:** `main.py`에서 `asyncio.create_task(bettor.run())`
- **연결:** WebSocket (이벤트 수신) + REST API (베팅)
- **전략:**
  - `day_discussion`과 `day_vote` 페이즈에서만 베팅
  - 최소 확신 임계값: 0.6 (60%)
  - 베팅 간 30초 쿨다운
  - 금액 선형 스케일링: 확신 0.6 → $1, 확신 1.0 → $10
  - 잔고 보호: 베팅 금액은 남은 잔고 이하로 제한
- **플레이하지 않는다.** AI Bettor는 베팅만 한다.
- **X402 서명:** 현재 TODO — 구조는 완성이지만 `_place_bet_via_api()`의 X402 결제 헤더 생성이 미구현.

**비유:** House AI가 플레이어에게 있어 하우스의 선수라면, AI Bettor는 베터에게 있어 하우스의 도박사다. 둘 다 서버 내부 AI이고, 둘 다 GPT-4o-mini를 사용하며, OpenAI 외에 외부 의존이 없다.

---

## 게임 라이프사이클 플로차트

```mermaid
flowchart TD
    Start([서버 시작]) --> Lobby[LOBBY 페이즈<br/>플레이어 참가]

    Lobby -->|7명 또는 타임아웃| Start_Game{게임 자동 시작}
    Start_Game -->|역할 배정| Night[NIGHT 페이즈<br/>마피아 킬<br/>탐정 조사]

    Night --> Day_Discussion[DAY_DISCUSSION 페이즈<br/>플레이어당 발언 2회<br/>AI Oddsmaker 분석]

    Day_Discussion --> Day_Vote[DAY_VOTE 페이즈<br/>각 플레이어 투표<br/>과반수 탈락]

    Day_Vote --> Win_Check{승리 조건?}

    Win_Check -->|마피아 전원 사망| Citizens_Win[시민 승리]
    Win_Check -->|마피아 ≥ 시민| Mafia_Win[마피아 승리]
    Win_Check -->|게임 계속| Night

    Citizens_Win --> Game_Over[GAME_OVER 페이즈<br/>승자 발표<br/>side_win 정산]
    Mafia_Win --> Game_Over

    Game_Over --> Reveal[REVEAL 페이즈<br/>플레이어 정체 공개<br/>is_ai_or_human 정산]

    Reveal --> Settlement{정산<br/>활성화?}
    Settlement -->|Yes| USDC[USDC 전송<br/>온체인으로 승자에게]
    Settlement -->|No| End
    USDC --> End([세션 종료])

    style Start fill:#3b82f6,stroke:#1e40af,color:#fff
    style Lobby fill:#10b981,stroke:#059669,color:#fff
    style Night fill:#1e293b,stroke:#0f172a,color:#fff
    style Day_Discussion fill:#f59e0b,stroke:#d97706,color:#000
    style Day_Vote fill:#ef4444,stroke:#dc2626,color:#fff
    style Citizens_Win fill:#10b981,stroke:#059669,color:#fff
    style Mafia_Win fill:#ef4444,stroke:#dc2626,color:#fff
    style Game_Over fill:#6b7280,stroke:#4b5563,color:#fff
    style Reveal fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style USDC fill:#ec4899,stroke:#db2777,color:#fff
```

### 페이즈 상세

#### **LOBBY** 페이즈
- 플레이어가 WebSocket (`join_lobby`) 또는 REST API (`/api/lobby/join-agent`)로 참가
- 남은 슬롯은 House AI로 자동 충원 (고유 성격)
- 타임아웃: `LOBBY_TIMEOUT_SECONDS` (기본 300초) → 현재 인원으로 자동 시작
- 7명 도달 시: 즉시 게임 시작

#### **NIGHT** 페이즈
- **마피아**: 제거 대상 선택 (`night_action`)
- **탐정**: 조사 대상 선택, 역할 확인
- **시민**: 수면 (행동 없음)
- 모든 행동은 동시, 밤 종료 시 해결
- `elimination` 이벤트 브로드캐스트 (피해자 이름 + 역할)

#### **DAY_DISCUSSION** 페이즈
- 각 플레이어 **2회 발언** (200자 제한)
- House AI는 GPT-4o-mini로 성격 맥락과 함께 대화 생성
- 휴먼/에이전트는 60초 타임아웃의 `action_request` 수신
- 발언은 `agent_message` 이벤트로 브로드캐스트
- AI Oddsmaker가 발언 분석 → `odds_update`로 배당률 갱신

#### **DAY_VOTE** 페이즈
- 각 플레이어가 한 명에게 투표 (자신 투표 불가)
- House AI는 GPT-4o-mini로 판단 (메모리 + 의심 고려)
- 휴먼/에이전트는 후보 중 선택, 60초 타임아웃
- 과반수 투표로 탈락
- 동표: 동점자 중 랜덤 선택
- `vote_cast` + `elimination` 이벤트 브로드캐스트

#### **GAME_OVER** 페이즈
- 승자 발표 (`game_over` 이벤트 + 페이아웃)
- `side_win`, `next_elimination`, `is_mafia` 베팅 정산

#### **REVEAL** 페이즈
- 플레이어 타입 공개 (HOUSE_AI, MOLTBOOK_AGENT, AGENT_HUMAN, HUMAN)
- `is_ai_or_human` 베팅 정산
- `identity_reveal` 이벤트 브로드캐스트
- `settlement_enabled=true`이면 USDC 온체인 정산

---

## 베팅 시스템 (X402 통합)

### 베팅 유형

| 베팅 유형 | 대상 | 타이밍 | 정산 |
|----------|------|--------|------|
| **side_win** | `"citizens"` 또는 `"mafia"` | GAME_OVER 전 언제든 | 승자 발표 시 |
| **next_elimination** | 플레이어 이름 (생존자) | DAY_VOTE 종료 전 | 다음 탈락자 공개 시 |
| **is_mafia** | 플레이어 이름 (생존자) | 해당 플레이어 사망 전 | 역할 공개 시 |
| **is_ai_or_human** | `"PlayerName:ai"` 또는 `"PlayerName:human"` | REVEAL 전 | REVEAL 페이즈 |

### 파리뮤추얼 페이아웃 로직

1. **풀 생성**: 각 bet_type의 모든 베팅이 공유 풀에 합산
2. **하우스 엣지**: 서버가 총 풀의 5% 차감
3. **승리 풀**: 95%를 승자에게 분배
4. **조기 베팅 보너스**:
   - 라운드 0 (로비/밤 1): 1.5× 가중치
   - 라운드 1 (첫 번째 낮): 1.2× 가중치
   - 라운드 2+: 1.0× 가중치
5. **페이아웃 공식**:
   ```python
   prize_pool = total_pool * 0.95          # 5% 하우스 엣지
   weighted_amount = bet.amount * bet.weight
   payout = (weighted_amount / total_weighted) * prize_pool
   ```

### X402 결제 프로토콜

모든 베팅에 X402 USDC 결제가 필요하다. 누가 베팅하든 플로우는 동일하다:

```
베터 → POST /api/bets (x-payment 헤더 없음)
    ← 402 Payment Required
       {amount, payTo: 서버_지갑, network: eip155:10143, asset: USDC}

베터 → X402 Facilitator: 결제 증명 요청
    ← 서명된 증명 {signature, tx_hash, payer_address}

베터 → POST /api/bets + x-payment 헤더
    → X402 미들웨어: 서명 검증, payer_address & amount 추출
    → request.state.x402_payment = {payer_address, amount_usdc, tx_hash}
    → BettingManager.place_bet(bettor_address=payer_address, ...)
    ← 200 OK {bet_id, amount, weight, odds}
```

### AI Oddsmaker

GPT-4o-mini가 매 페이즈 전환 시 게임 상태를 분석:

**입력:** 현재 페이즈, 라운드, 생존/사망 에이전트, 최근 발언, 투표 이력

**출력:**
```json
{
  "mafia_prob": 0.35,
  "citizen_prob": 0.65,
  "suspects": [
    {"name": "Viktor", "suspicion": 0.8, "reasoning": "공격적 회피"},
    {"name": "Luna", "suspicion": 0.3, "reasoning": "일관된 행동"}
  ]
}
```

배당률은 블렌딩: AI 분석 70% + 실제 베팅 분포에서 추론한 시장 배당률 30%.

`odds_update` WebSocket 이벤트로 브로드캐스트 → 모든 연결 클라이언트의 베팅 UI 갱신.

### 정산 흐름

```
GAME_OVER
    → BettingManager.settle(winner) → {wallet_address: payout_usdc}
        → side_win, next_elimination, is_mafia 풀

REVEAL
    → BettingManager.settle_identity_bets(players)
        → is_ai_or_human 풀
        → HOUSE_AI / MOLTBOOK_AGENT → "ai"
        → AGENT_HUMAN / HUMAN → "human"

합산 페이아웃
    → settlement_enabled=true?
        → USDCSettlement.settle_payouts(combined_payouts)
        → ERC-20 transfer()로 각 승자 지갑에 전송
        → usdc_settlement 이벤트 브로드캐스트 (전송 건별 tx_hash)
```

---

## WebSocket 이벤트 맵

### 서버 → 클라이언트 이벤트 (15개)

| 이벤트 | 데이터 필드 | UI 효과 |
|--------|-----------|---------|
| **phase_change** | `phase`, `round` | 배경 크로스페이드, 틴트 오버레이 변경 |
| **agent_message** | `agent`, `message` | 플레이어 카드에 채팅 버블 (5초 자동 소멸) |
| **vote_cast** | `voter`, `target` | 대상 카드에 투표 오버레이, 뱃지 카운트 증가 |
| **elimination** | `name`, `role`, `reason` | 플레이어 카드에 해골 오버레이 |
| **game_over** | `winner`, `rounds`, `alive_agents`, `payouts` | confetti 애니메이션, 승자 발표 |
| **odds_update** | `mafia_prob`, `citizen_prob`, `suspects` | 베팅 패널 배당률 표시 갱신 |
| **lobby_joined** | `name`, `success` | "You joined as {name}" |
| **lobby_status** | `players`, `count`, `ready` | 플레이어 슬롯 갱신, 카운터 "3/7" |
| **game_starting** | `player_count` | 카운트다운 모달 → 게임 화면 전환 |
| **action_request** | `prompt`, `actionType`, `options`, `timeout` | ActionPanel (textarea/드롭다운/버튼) + 타이머 |
| **identity_reveal** | `agent`, `player_type`, `role` | 플레이어 카드 뱃지 갱신 (AI/Human 아이콘) |
| **bet_placed** | `bet_id`, `amount`, `target` | "My Bets" 목록에 추가 |
| **bet_confirmed** | `bet_id` | 녹색 체크마크, 페이아웃 표시 |
| **bet_rejected** | `bet_id` | 빨간 X, 손실 표시 |
| **usdc_settlement** | `transfers` (주소, 금액, tx_hash) | Monad 익스플로러 링크가 있는 토스트 |

### 클라이언트 → 서버 이벤트 (3개)

| 이벤트 | 데이터 필드 | 트리거 | 목적 |
|--------|-----------|--------|------|
| **join_lobby** | `type` ("human" \| "agent_human"), `name` | "Join Game" 클릭 | 플레이어 등록 |
| **action_response** | `type` ("statement" \| "vote" \| "night_action"), `player_name`, `response` | ActionPanel 제출 | 플레이어 결정 전송 |
| **ping** | — | 30초 간격 | WebSocket 유지 |

---

## 화면 상태 머신

```mermaid
stateDiagram-v2
    [*] --> landing: 페이지 로드

    landing --> lobby: "Play" 또는 "Spectate" 클릭

    lobby --> game: game_starting 이벤트<br/>(플레이어인 경우)
    lobby --> spectate: game_starting 이벤트<br/>(관전자인 경우)

    game --> reveal: phase === "reveal"
    spectate --> reveal: phase === "reveal"

    reveal --> game: 다음 라운드 시작<br/>(phase === "night")
    reveal --> spectate: 다음 라운드 시작<br/>(관전자 뷰)

    game --> game_over: game_over 이벤트
    spectate --> game_over: game_over 이벤트

    game_over --> landing: "Play Again" 클릭

    state landing {
        [*] --> title_screen
        title_screen --> enter_name: "Join Game" 클릭
        enter_name --> [*]: 이름 제출
    }

    state lobby {
        [*] --> waiting
        waiting --> countdown: 7명 참가
        countdown --> [*]: 게임 시작
    }

    state game {
        [*] --> night
        night --> day_discussion
        day_discussion --> day_vote
        day_vote --> night: 게임 계속
        day_vote --> [*]: 승리 조건 충족
    }

    state spectate {
        [*] --> watching
        watching --> betting
        betting --> watching
    }

    style landing fill:#3b82f6,stroke:#1e40af,color:#fff
    style lobby fill:#10b981,stroke:#059669,color:#fff
    style game fill:#f59e0b,stroke:#d97706,color:#000
    style spectate fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style reveal fill:#ec4899,stroke:#db2777,color:#fff
    style game_over fill:#6b7280,stroke:#4b5563,color:#fff
```

### 화면 라우팅 로직

| 화면 | 조건 | 렌더링 컴포넌트 |
|------|------|--------------|
| **landing** | `gameStore.screen === 'landing'` | `LandingScreen` (깨진 마스크 이펙트, "Play" / "Spectate" 버튼) |
| **lobby** | `gameStore.screen === 'lobby'` | `LobbyScreen` (플레이어 슬롯, 카운트다운, "Join Game" 폼) |
| **game** | `gameStore.screen === 'game' && gameStore.isPlayer` | `GameLayout` (Header, Background, GameBoard, ChatPanel, BettingPanel, ActionPanel) |
| **spectate** | `gameStore.screen === 'game' && !gameStore.isPlayer` | `SpectatorScreen` (플레이어 그리드, 게임 로그, 베팅 터미널, 관전자 채팅) |
| **reveal** | `gameStore.phase === 'reveal'` | `RevealScreen` (AI/Human 라벨 3D 카드 플립 애니메이션) |
| **game_over** | `gameStore.screen === 'game_over'` | `GameOverScreen` (승자 발표, confetti, 최종 베팅 결과, "Play Again") |

---

## UI 컴포넌트 트리

```mermaid
graph TB
    App[App.tsx]

    App --> Landing[LandingScreen]
    App --> Lobby[LobbyScreen]
    App --> GameLayout
    App --> Spectate[SpectatorScreen]
    App --> Reveal[RevealScreen]
    App --> GameOver[GameOverScreen]

    Landing --> LandingBG[깨진 마스크 이펙트]
    Landing --> PlayBtn[Play / Spectate 버튼]

    Lobby --> LobbySlots[PlayerSlot × 7]
    Lobby --> JoinForm[JoinForm]
    Lobby --> Countdown[CountdownModal]

    GameLayout --> Header
    GameLayout --> Background[Background<br/>낮/밤 이미지]
    GameLayout --> PhaseTint[PhaseTintOverlay<br/>파랑/앰버/빨강]
    GameLayout --> NightOverlay[NightOverlay<br/>별 + 달]
    GameLayout --> GameBoard
    GameLayout --> ChatPanel
    GameLayout --> BettingPanel
    GameLayout --> BettingStatusBar
    GameLayout --> EmoteMenu
    GameLayout --> MobileTab[MobileTabBar]

    GameBoard --> PlayerCard[PlayerCard × 7]

    PlayerCard --> Portrait[초상화 이미지<br/>AVATAR_IMAGES 배열]
    PlayerCard --> ChatBubble[채팅 버블 오버레이<br/>카드 내부, 금테]
    PlayerCard --> EmoteOverlay[이모트 오버레이<br/>스프링 애니메이션]
    PlayerCard --> VoteOverlay[투표 오버레이<br/>카운트 뱃지]
    PlayerCard --> RoleBadge[역할 뱃지<br/>검/눈/방패]
    PlayerCard --> DeadSkull[사망 해골 오버레이]

    ChatPanel --> Messages[ChatMessage × N]

    BettingPanel --> BetTabs[베팅 유형 탭 × 4]
    BettingPanel --> BetSlip[BetSlip]
    BettingPanel --> MyBets[My Bets 목록]

    Spectate --> SpectGrid[플레이어 그리드 3×3]
    Spectate --> GameLog[게임 로그 15개]
    Spectate --> BetTerminal[베팅 터미널]
    Spectate --> SpecChat[관전자 채팅<br/>플로팅 패널]

    BetTerminal --> QuickAmounts[빠른 금액 버튼]
    BetTerminal --> PayoutCalc[페이아웃 계산기]

    Reveal --> CardFlip[3D 카드 플립 애니메이션 × 7]

    GameOver --> WinnerMsg[승자 발표]
    GameOver --> Confetti[Canvas Confetti]
    GameOver --> FinalBets[최종 베팅 결과]

    style App fill:#3b82f6,stroke:#1e40af,color:#fff
    style GameLayout fill:#10b981,stroke:#059669,color:#fff
    style PlayerCard fill:#f59e0b,stroke:#d97706,color:#000
    style Portrait fill:#ec4899,stroke:#db2777,color:#fff
    style ChatBubble fill:#fbbf24,stroke:#f59e0b,color:#000
    style BettingPanel fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Spectate fill:#06b6d4,stroke:#0891b2,color:#fff
```

---

## 상태 관리 (Zustand 스토어 4개)

### 1. gameStore

```typescript
interface GameStore {
  // 핵심 게임 상태
  phase: Phase
  round: number
  players: Player[]
  votes: Record<string, string>  // 투표자 → 대상
  winner: string | null  // "citizens" | "mafia"

  // 플레이어 아이덴티티
  isPlayer: boolean
  myPlayerName: string | null

  // 로비 상태
  lobbyPlayers: LobbyPlayer[]
  lobbyCount: number
  lobbyReady: boolean

  // 액션 요청
  actionRequest: ActionRequest | null

  // 화면 라우팅
  screen: 'landing' | 'lobby' | 'game' | 'game_over'

  // 사용자 설정
  nickname: string
  avatarIndex: number
  isSpectator: boolean

  // 비주얼 이펙트
  activeEmotes: Record<string, string>     // playerName → 이모지
  chatBubbles: Record<string, { message: string; expiresAt: number }>
  voteCounts: Record<string, number>       // 대상 → 카운트
  showVoteUI: boolean
  selectedVoteTarget: string | null
}
```

### 2. chatStore

```typescript
interface ChatStore {
  messages: ChatMessage[]
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
}

interface ChatMessage {
  id: string
  agent: string
  message: string
  timestamp: string
  type: 'statement' | 'system' | 'spectator'
}
```

### 3. bettingStore

```typescript
interface BettingStore {
  odds: OddsBoard | null
  bets: Bet[]
  balance: number  // USDC 잔고

  setOdds: (odds: OddsBoard) => void
  addBet: (bet: Bet) => void
  updateStatus: (betId: string, status: BetStatus) => void
  setBalance: (balance: number) => void
}
```

### 4. walletStore

```typescript
interface WalletStore {
  connected: boolean
  address: string | null
  balance: string | null  // USDC 잔고
  txStatus: 'idle' | 'pending' | 'success' | 'error'

  connect: () => Promise<void>
  disconnect: () => void
  placeBet: (betData: BetData) => Promise<string>
  claimWinnings: (gameId: string) => Promise<string>
}
```

---

## 페이즈 비주얼 전환

| 페이즈 | 배경 | 틴트 오버레이 | 특수 효과 |
|--------|------|-------------|----------|
| **lobby** | — | — | — |
| **night** | `game-bg-night.png` (크로스페이드 2초) | 파랑 `#0a0e1f/60%` | NightOverlay (Canvas 별 + 달 애니메이션) |
| **day_discussion** | `game-bg.png` (크로스페이드 2초) | 앰버 `#0a0a05/50%` | — |
| **day_vote** | `game-bg.png` | 빨강 `#1a0505/70%` | "Voting Time" 투표 오버레이 |
| **reveal** | `game-bg.png` | 보라 `#4c1d95/60%` | 3D 카드 플립 (AI/Human 표시) |
| **game_over** | `game-bg.png` | 에메랄드 `#064e3b/60%` (시민) 또는 빨강 `#7f1d1d/60%` (마피아) | Canvas confetti (300개, 3초) |

### 배경 크로스페이드

```typescript
const backgroundVariants = {
  day: {
    backgroundImage: 'url(/game-bg.png)',
    transition: { duration: 2, ease: 'easeInOut' }
  },
  night: {
    backgroundImage: 'url(/game-bg-night.png)',
    transition: { duration: 2, ease: 'easeInOut' }
  }
}

<motion.div variants={backgroundVariants} animate={phase === 'night' ? 'night' : 'day'} />
```

---

## 데스크톱 & 모바일 레이아웃

### 데스크톱 (lg+)

```
┌──────────────────────────────────────────────────────────────────┐
│ [Header: 로고 | 페이즈 뱃지 | 라운드 | 타이머]                      │
├────────────────┬─────────────────────┬───────────────────────────┤
│ 플레이어        │ 게임 보드            │ 베팅                       │
│ (280px 고정)   │ (flex-1)            │ (320px 고정)               │
│                │                     │                           │
│ [PlayerCard]   │ ┌─────────────────┐ │ [베팅 유형 탭]              │
│ [PlayerCard]   │ │ PlayerCard × 7  │ │ [대상 드롭다운]             │
│ [PlayerCard]   │ │ (초상화 이미지)   │ │ [빠른 금액]                │
│ [PlayerCard]   │ │ 채팅 버블        │ │ [페이아웃 계산]             │
│ [PlayerCard]   │ │ 이모트 오버레이   │ │ [Place Bet 버튼]           │
│ [PlayerCard]   │ │ 투표 뱃지        │ │ [My Bets 목록]             │
│ [PlayerCard]   │ └─────────────────┘ │                           │
│                │                     │ [배당률 바]                 │
│ [채팅 패널]     │                     │ 시민 65% | 마피아 35%       │
└────────────────┴─────────────────────┴───────────────────────────┘
│ [BettingStatusBar — 하단 중앙, 80% 너비]                           │
│ 현재 베팅: 3 | 총 베팅액: $12 | 예상 페이아웃: $18.50              │
└──────────────────────────────────────────────────────────────────┘
```

### 모바일 (<lg)

```
┌──────────────────────────┐
│ [Header]                 │
├──────────────────────────┤
│                          │
│ [PlayerCard 그리드 2×4]   │
│ - 초상화 이미지            │
│ - 카드 내 채팅 버블         │
│ - 이모트 오버레이           │
│ - 투표 뱃지               │
│                          │
├──────────────────────────┤
│ [하단 탭 바]              │
│ [Game] [Chat] [Bet]      │
└──────────────────────────┘

탭 1: Game — PlayerCard 그리드 + ActionPanel
탭 2: Chat — 풀스크린 채팅 메시지
탭 3: Bet  — 베팅 터미널 + 배당률 + My Bets
```

MobileTabBar: 하단 고정, 3탭 (Users, MessageCircle, DollarSign 아이콘), `<lg` 브레이크포인트에서만 표시.

---

## 모듈 책임 맵

| 모듈 | 용도 | 핵심 파일 |
|------|------|----------|
| **src/config/** | 설정, enum, 상수 | `settings.py` (Pydantic BaseSettings), `constants.py` (Role, Phase, PlayerType, BetType) |
| **src/models/** | Pydantic frozen 모델 | `game.py`, `agent.py`, `betting.py`, `events.py` — 전부 `frozen=True` |
| **src/engine/** | 게임 상태 머신 | `game_engine.py`, `phase_handlers.py`, `role_assigner.py`, `win_checker.py` |
| **src/agents/** | AI 성격 | `personalities.py` (7종), `prompts.py`, `llm_client.py`, `memory.py` |
| **src/players/** | PlayerProtocol 구현 | `protocol.py`, `house_ai.py`, `moltbook_agent.py`, `agent_human.py`, `human.py` |
| **src/lobby/** | 로비 관리 | `manager.py` (LobbyManager) |
| **src/moltbook/** | 외부 에이전트 연동 | `client.py` (DM API), `auth.py` (Identity JWT 검증) |
| **src/betting/** | 파리뮤추얼 베팅 | `pool.py`, `odds.py`, `manager.py`, `oddsmaker.py`, `settlement.py` |
| **src/blockchain/** | Web3 연동 | `provider.py` (AsyncWeb3 + POA), `contract.py` (오라클 연산) |
| **src/x402/** | USDC 결제 프로토콜 | `middleware.py` (402 Payment Required), `models.py` (frozen) |
| **src/ai_bettor/** | 자율 베팅 | `client.py` (WebSocket 오케스트레이터), `analyzer.py` (LLM), `strategy.py`, `models.py` |
| **src/api/** | FastAPI 서버 | `server.py`, `routes.py`, `ws_manager.py` |
| **src/storage/** | 데이터베이스 계층 | `database.py` (aiosqlite), `repositories/` |
| **src/utils/** | 유틸리티 | `logger.py` (structlog), `retry.py`, `errors.py` |

---

## 선택 기능 설정

아래 기능은 전부 **기본 비활성화**. `.env`로 활성화.

### X402 USDC 베팅

```bash
X402_ENABLED=true
X402_FACILITATOR_URL=https://x402-facilitator.molandak.org
X402_NETWORK=eip155:10143
X402_USDC_ADDRESS=0x534b2f3A21130d7a60830c2Df862319e593943A3
X402_PAY_TO=0x...서버-지갑
```

요구사항: Monad 테스트넷 USDC, X402 facilitator 서비스, MetaMask (휴먼용).

### 블록체인 온체인 정산

```bash
SETTLEMENT_ENABLED=true
SETTLEMENT_PRIVATE_KEY=0x...서버-지갑-키
BLOCKCHAIN_RPC_URL=https://testnet-rpc.monad.xyz
BLOCKCHAIN_CHAIN_ID=10143
```

요구사항: [Monad Faucet](https://faucet.monad.xyz)에서 MON 토큰, USDC가 충전된 서버 지갑.

### Moltbook 외부 에이전트

```bash
MOLTBOOK_API_URL=https://api.moltbook.io
MOLTBOOK_APP_KEY=moltdev_xxx
MOLTBOOK_AUDIENCE=mafia-ai.example.com
LOBBY_TIMEOUT_SECONDS=300
```

요구사항: Moltbook 개발자 앱 키, 등록된 에이전트.

### AI Bettor (자율 베팅)

```bash
AI_BETTOR_ENABLED=true
AI_BETTOR_BUDGET_USDC=50.0
AI_BETTOR_PRIVATE_KEY=0x...선택사항
```

동작: WebSocket 관전, GPT-4o-mini 분석, 확신도 ≥ 0.6일 때 베팅, `day_discussion`/`day_vote` 페이즈만, 30초 쿨다운.

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| **OpenAI API 오류** | 잘못된 키, 레이트 리밋 | `.env` OPENAI_API_KEY 확인, 쿼터 확인 |
| **WebSocket 끊김** | 네트워크 불안정 | 지수 백오프 자동 재연결 (내장) |
| **프론트엔드 안 뜸** | 빌드 안 함 | `cd frontend && npm run build` |
| **로비에서 멈춤** | 인원 부족, 타임아웃 미도달 | 타임아웃 대기 또는 인원 추가 |
| **/api/bets에서 402** | X402 미활성화 또는 결제 헤더 없음 | `.env`에 `X402_ENABLED=true` 설정 |
| **X402 결제 오류** | MetaMask 미연결, USDC 부족 | 지갑 연결, faucet에서 USDC 확보 |
| **DB 잠김** | 동시 쓰기 | `data/mafia-ai.db` 삭제 후 재시작 |
| **블록체인 tx 실패** | MON 부족 | faucet에서 MON 확보, Chain ID 10143 확인 |
| **AI Bettor 베팅 안 함** | 확신도 < 0.6, 잘못된 페이즈, 쿨다운 | 로그에서 확신도 점수 확인 |
| **Moltbook 에이전트 참가 실패** | 잘못된 JWT, 잘못된 앱 키 | `MOLTBOOK_APP_KEY`와 에이전트 등록 확인 |

---

## 성능

- **AsyncIO**: 모든 I/O 비동기 (OpenAI API, SQLite, WebSocket)
- **지연 평가**: 배당률은 페이즈 전환 시에만 계산
- **개별 셀렉터**: Zustand 셀렉터로 불필요한 리렌더 방지
- **Canvas 렌더링**: NightOverlay는 Canvas API 사용 (DOM 아님)
- **GPT-4o-mini**: 게임당 ~$0.05 (~100 API 호출)
- **SQLite**: 데이터베이스 호스팅 비용 0

---

## 보안

- **레이트 리밋**: 베팅 엔드포인트 IP당 10 req/min
- **입력 검증**: Pydantic 모델로 타입 강제
- **SQL 인젝션**: 매개변수화된 쿼리만 사용
- **비밀 키**: 환경 변수만 사용 (커밋 금지)
- **X402 검증**: 암호화 서명 검증
- **XSS 방지**: React 자동 이스케이프, `dangerouslySetInnerHTML` 미사용
- **Moltbook Identity**: 서버 사이드 API 호출을 통한 JWT 검증

---

## 참조

- **OpenAI API**: https://platform.openai.com/docs
- **Monad Docs**: https://docs.monad.xyz/
- **X402 Protocol**: https://x402.org/
- **Moltbook API**: https://moltbook.io/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **React 19**: https://react.dev/
- **Zustand**: https://docs.pmnd.rs/zustand/
- **Framer Motion**: https://www.framer.com/motion/
- **Tailwind CSS v4**: https://tailwindcss.com/
- **Pydantic v2**: https://docs.pydantic.dev/
