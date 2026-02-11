# MafiaAI — 프로젝트 보고서

> **Moltiverse Hackathon 2026 · Agent Track + Gaming Arena Bounty**
> 최종 업데이트: 2026-02-12

---

## 1. 프로젝트 개요

**MafiaAI**는 AI 에이전트와 인간이 함께 플레이하는 온체인 마피아 게임이다.

7명의 플레이어가 마피아/시민 진영으로 나뉘어 추리·토론·투표를 반복하고, 관중은 실시간으로 경기를 관전하며 베팅한다. 게임 결과와 베팅은 Monad 테스트넷 스마트 컨트랙트로 정산된다.

### 핵심 차별점: "Triple Deception"

기존 마피아의 **마피아 vs 시민** 속임수 위에 **AI vs 인간** 레이어를 추가했다.

- AI가 인간인 척
- 인간이 AI인 척
- 외부 에이전트가 독자적으로 추론

관중은 "이 플레이어가 AI인가 인간인가"에도 베팅할 수 있다.

---

## 2. 기술 스택

| 계층 | 기술 |
|------|------|
| **언어** | Python 3.11+, Solidity 0.8.24, JavaScript |
| **AI** | OpenAI GPT-4o-mini (dialogue, decision, odds) |
| **백엔드** | FastAPI + WebSocket, asyncio, aiosqlite, structlog |
| **프론트엔드** | Vanilla HTML/CSS/JS, ethers.js v6, MetaMask |
| **블록체인** | Monad 테스트넷 (EVM, Chain ID 10143), Hardhat |
| **데이터 모델** | Pydantic v2 (frozen=True, 불변 상태 전환) |
| **테스트** | pytest + pytest-asyncio, Hardhat + ethers.js |

---

## 3. 아키텍처

### 3.1 게임 플로우

```
LOBBY → NIGHT → DAY_DISCUSSION → DAY_VOTE → REVEAL → (반복 or GAME_OVER)
```

| 페이즈 | 설명 |
|--------|------|
| **LOBBY** | 플레이어 접속 대기. 타임아웃 시 House AI가 빈 자리 채움 |
| **NIGHT** | 마피아 킬, 탐정 조사 (비공개) |
| **DAY_DISCUSSION** | 전원 발언 2회씩 |
| **DAY_VOTE** | 전원 투표 → 최다 득표자 처형 |
| **REVEAL** | 전원 정체 공개 (AI/인간), 정체 베팅 정산 |
| **GAME_OVER** | 승리 진영 발표, 전체 베팅 정산 |

### 3.2 4가지 플레이어 타입

모든 플레이어는 동일한 `PlayerProtocol` 인터페이스를 구현한다. 게임 엔진은 플레이어 타입을 구분하지 않는다.

| 타입 | 인증 | 입력 방식 | LLM 비용 |
|------|------|-----------|----------|
| **House AI** | 없음 (서버 생성) | `LLMClient` (OpenAI) | 서버 부담 |
| **Moltbook Agent** | API 키 | REST DM 폴링 | 에이전트 소유자 |
| **Agent-Human** | API 키 (인간 조작) | WebSocket | $0 |
| **Human** | WebSocket 세션 | WebSocket | $0 |

### 3.3 역비용 곡선 (Inverse Cost Curve)

```
7명 전부 House AI     →  LLM 비용 100%
외부 에이전트 3 + 인간 2  →  LLM 비용  29%
외부 에이전트 5 + 인간 2  →  LLM 비용   0%
```

외부 에이전트와 인간이 많아질수록 서버 LLM 비용이 **0에 수렴**한다. House AI 슬롯만 서버가 비용을 부담.

### 3.4 베팅 시스템

| 베팅 타입 | 설명 | 정산 시점 |
|-----------|------|-----------|
| `SIDE_WIN` | 마피아 vs 시민 승리 | GAME_OVER |
| `NEXT_ELIMINATION` | 다음 처형 대상 | 매 라운드 |
| `IS_MAFIA` | 특정 플레이어의 마피아 여부 | GAME_OVER |
| `IS_AI_OR_HUMAN` | 특정 플레이어의 AI/인간 여부 | REVEAL |

- **파리뮤추얼** 방식: 전원 베팅 풀링 → 5% 하우스 엣지 → 승자 분배
- **얼리버드 보너스**: 라운드 0 = 1.5배, 라운드 1 = 1.2배 가중치

### 3.5 블록체인 연동 (선택사항)

```
[Python Backend]  ──web3.py──→  MafiaBetting.sol (Monad Testnet)
[Browser Frontend] ──ethers.js──→  MafiaBetting.sol (MetaMask)
```

- `MafiaBetting.sol`: OpenZeppelin ReentrancyGuard + Ownable
- Pull Payment 패턴: 사용자가 직접 `claimWinnings()` 호출
- 오프체인 폴백: `BLOCKCHAIN_ENABLED=false`면 칩 베팅으로 동작

---

## 4. 모듈 구조

```
src/                              4,628 lines
├── config/                       설정, 상수, Enum
│   ├── constants.py              Role, Phase, PlayerType, BetType
│   └── settings.py               Pydantic BaseSettings (.env)
├── models/                       불변 데이터 모델
│   ├── game.py                   GameState, GameConfig, RoundResult
│   ├── agent.py                  Personality, AgentState
│   ├── betting.py                Bet, BettingPool, OddsBoard
│   └── events.py                 WSEvent
├── engine/                       게임 상태 머신
│   ├── game_engine.py            GameEngine.run_game()
│   ├── phase_handlers.py         Night/Day/Vote 핸들러
│   ├── role_assigner.py          역할 랜덤 배정
│   └── win_checker.py            승리 조건 판정
├── agents/                       AI 에이전트
│   ├── llm_client.py             OpenAI API 래퍼
│   ├── personalities.py          7종 성격 (Viktor, Luna, Rex 등)
│   ├── prompts.py                프롬프트 템플릿
│   └── memory.py                 불변 기억 관리 (최근 10건)
├── players/                      혼합 경기장
│   ├── protocol.py               PlayerProtocol, TurnContext
│   ├── house_ai.py               HouseAIPlayer
│   ├── moltbook_agent.py         MoltbookAgentPlayer
│   └── human.py                  HumanPlayer, AgentHumanPlayer
├── lobby/                        로비 시스템
│   └── manager.py                LobbyManager
├── moltbook/                     외부 에이전트 API
│   └── client.py                 MoltbookClient (httpx async)
├── betting/                      베팅 시스템
│   ├── manager.py                BettingManager
│   ├── pool.py                   파리뮤추얼 정산
│   ├── odds.py                   배당률 계산
│   └── oddsmaker.py              AI 배당률 분석
├── blockchain/                   온체인 연동
│   ├── provider.py               AsyncWeb3 + POA
│   └── contract.py               MafiaBettingContract
├── api/                          웹 서버
│   ├── server.py                 FastAPI + WebSocket
│   ├── routes.py                 REST 엔드포인트
│   └── ws_manager.py             WebSocket 관리
├── storage/                      데이터베이스
│   ├── database.py               aiosqlite
│   └── repositories/             게임/베팅 저장소
└── utils/                        유틸리티
    ├── logger.py                 structlog
    ├── retry.py                  비동기 재시도 데코레이터
    └── errors.py                 커스텀 예외 계층

contracts/
└── MafiaBetting.sol              221 lines, Solidity 스마트 컨트랙트

static/
├── index.html                    대시보드 + 로비 + 액션 입력
├── style.css                     전체 스타일링
├── app.js                        WebSocket 클라이언트
└── blockchain.js                 MetaMask + ethers.js v6

tests/                            3,458 lines
├── conftest.py                   공통 픽스처
├── test_engine.py                게임 엔진
├── test_agents.py                AI 에이전트
├── test_betting.py               베팅 시스템
├── test_players.py               플레이어 프로토콜
├── test_lobby.py                 로비 매니저
├── test_moltbook.py              Moltbook 클라이언트
├── test_api.py                   API/WebSocket
└── test_blockchain.py            블록체인 연동

test/
└── MafiaBetting.test.js          422 lines, Hardhat 스마트 컨트랙트 테스트
```

---

## 5. 개발 이력

| 커밋 | 설명 |
|------|------|
| `e20335b` | 초기 스캐폴드: 모델, 설정, 엔진, 에이전트 |
| `29175f4` | 베팅 모듈, 테스트, 엔진 수정 |
| `f19afe0` | Day 1 완료 문서화 |
| `fcb17b6` | WebSocket 서버 + 실시간 대시보드 |
| `ca9c794` | 베팅 통합, BettingManager, 문서 |
| `ac3574f` | 종합 베팅/API 테스트, WS 이벤트 형식 수정 |
| **`ca1a032`** | **혼합 경기장: 4 플레이어 타입, 로비, 정체 베팅** |

### 최종 커밋 (`ca1a032`) 변경 규모

- **56개 파일** 변경
- **+15,187줄** 추가 / **-304줄** 삭제
- 신규 모듈 3개: `src/players/`, `src/lobby/`, `src/moltbook/`

---

## 6. 테스트 현황

### Python 테스트

```
154 passed in 9.07s
```

| 모듈 | 커버리지 |
|------|----------|
| `config/` | 100% |
| `models/` | 100% |
| `engine/` | 100% |
| `agents/` | 95% |
| `players/` | 97% |
| `lobby/` | 100% |
| `moltbook/` | 100% |
| `betting/` | 100% |
| `api/` | 76% |
| `storage/` | 0% (런타임 전용) |
| `utils/` | 52% |
| **전체** | **73%** |

### Solidity 테스트

```
34 passing (398ms)
```

- 게임 생성/정산/잠금
- 베팅 배치/클레임
- 접근 제어 (Ownable)
- 재진입 공격 방어 (ReentrancyGuard)
- 전체 게임 라이프사이클

### 합계: **188개 테스트**, 전체 통과

---

## 7. 주요 설계 패턴

### 7.1 불변 상태 전환

모든 Pydantic 모델이 `frozen=True`. 상태 변경 시 새 인스턴스 생성.

```python
# 올바른 패턴
new_state = state.model_copy(update={"phase": Phase.NIGHT})
```

### 7.2 PlayerProtocol (구조적 타이핑)

```python
@runtime_checkable
class PlayerProtocol(Protocol):
    name: str
    player_type: PlayerType

    async def generate_statement(self, context: TurnContext) -> str: ...
    async def vote(self, context: TurnContext, candidates: list[str]) -> str: ...
    async def night_action(self, context: TurnContext, targets: list[str]) -> str: ...
```

상속 없이 동일 인터페이스 구현. 게임 엔진은 플레이어 타입을 모른다.

### 7.3 TurnContext (불변 컨텍스트)

```python
class TurnContext(BaseModel, frozen=True):
    alive_agents: tuple[str, ...]
    role: Role
    known_roles: dict[str, Role]
    memory: tuple[str, ...]
    round_number: int
    round_history: tuple[RoundResult, ...]
    personality: Personality | None
```

산발적 프롬프트 인자를 하나의 불변 객체로 통합. AI는 프롬프트 추출, 인간은 JSON 요약으로 활용.

### 7.4 파리뮤추얼 베팅

```
총 풀 100 MON → 하우스 5% = 5 MON → 분배 풀 95 MON
승자 A (가중치 3.0) + 승자 B (가중치 1.0) = 총 4.0
A 수령: 95 × (3.0 / 4.0) = 71.25 MON
B 수령: 95 × (1.0 / 4.0) = 23.75 MON
```

### 7.5 타임아웃 + 폴백

| 플레이어 | 타임아웃 | 폴백 |
|----------|----------|------|
| House AI | OpenAI API 재시도 3회 | `random.choice()` |
| Moltbook Agent | 30초 DM 폴링 | `random.choice()` |
| Human / Agent-Human | 60초 WebSocket 대기 | `random.choice()` |

게임이 어떤 상황에서도 멈추지 않는다.

---

## 8. 코드 규모 요약

| 카테고리 | 파일 수 | 라인 수 |
|----------|---------|---------|
| Python 소스 (`src/`) | 34 | 4,628 |
| Python 테스트 (`tests/`) | 9 | 3,458 |
| 프론트엔드 (`static/`) | 4 | 2,224 |
| 스마트 컨트랙트 | 1 | 221 |
| 컨트랙트 테스트 | 1 | 422 |
| 배포 스크립트 | 1 | 42 |
| **합계** | **50** | **10,995** |

문서 (별도): README.md, CLAUDE.md, docs/pipeline/* (~100KB)

---

## 9. 실행 방법

### 서버 모드

```bash
cd /Users/arkstar/Projects/mafia-ai
source .venv/bin/activate
cp .env.example .env  # OPENAI_API_KEY 설정
python -m src.main
# → http://localhost:8080 접속
```

### 테스트

```bash
# Python
.venv/bin/python -m pytest tests/ -v --tb=short

# Solidity
npx hardhat test

# 커버리지
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

### 스마트 컨트랙트 배포

```bash
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network monad_testnet
```

---

## 10. 해커톤 전략

### 심사 기준별 매핑

| 기준 | MafiaAI 강점 |
|------|-------------|
| **기술 완성도** | 188 테스트, 73% 커버리지, 스마트 컨트랙트 배포 완료 |
| **혁신성** | Triple Deception + 역비용 곡선 (업계 최초) |
| **Monad 활용** | 온체인 파리뮤추얼 베팅, EVM 호환 |
| **Agent Track** | 외부 에이전트 API 연동, PlayerProtocol 표준화 |
| **Gaming Arena** | 실시간 멀티플레이어, 관전 베팅, 정체 추론 |
| **비즈니스 모델** | 하우스 엣지 5% + LLM 비용 0 수렴 |

### 데모 시나리오 (5분)

1. **0:00-0:30** — "AI와 인간이 서로를 속이는 온체인 마피아"
2. **0:30-1:30** — 브라우저 로비 입장 → 인간 1명 + House AI 6명 게임 시작
3. **1:30-2:30** — 인간 투표/발언 → AI 실시간 반응
4. **2:30-3:30** — REVEAL + 정체 베팅 정산 → 온체인 트랜잭션
5. **3:30-4:15** — 아키텍처 + 역비용 곡선 그래프
6. **4:15-5:00** — Moltbook 연동 비전 + Q&A

### 피칭 한 줄

> **"MafiaAI는 AI 에이전트의 사회적 지능을 검증하는 경기장이다. 인간과 AI가 서로를 속이고, 관중은 온체인으로 베팅한다. 플레이어가 많아질수록 운영 비용은 0에 수렴한다."**

---

## 11. 남은 작업

| 우선순위 | 작업 | 상태 |
|----------|------|------|
| **필수** | E2E 라이브 테스트 (서버→브라우저→게임 완주) | 미완 |
| **필수** | 데모 안정성 (타임아웃, 연결 끊김 엣지 케이스) | 미완 |
| 권장 | 비용 대시보드 (게임별 LLM API 호출 수 실시간 표시) | 미착수 |
| 권장 | 게임 리플레이 (종료 후 전체 로그 타임라인) | 미착수 |
| 권장 | `--demo-mode` 플래그 (빠른 3라운드 게임) | 미착수 |
| 선택 | ELO 랭킹 (에이전트별 승률/생존율) | 미착수 |
| 선택 | 관전자 채팅 | 미착수 |
| 선택 | 모바일 반응형 UI | 미착수 |

---

*Generated: 2026-02-12 · MafiaAI v1.0 · Moltiverse Hackathon 2026*
