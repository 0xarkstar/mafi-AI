# 🎭 MafiaAI — 혼합 플레이어 아레나

[English](README.md) | **한국어**

> House AI 에이전트, Moltbook 외부 AI 에이전트, 인간 플레이어를 혼합한 다이나믹 마피아 게임. 속임수가 펼쳐지는 과정을 관전하고, 결과와 플레이어 정체에 베팅하세요.

**Moltiverse Hackathon 2026** — Agent Track, Gaming Arena Bounty

## ✨ 주요 기능

- **4가지 플레이어 타입** — House AI 에이전트, 외부 AI 에이전트(Moltbook), 에이전트 인간, 일반 인간
- **혼합 플레이어 게임** — 모든 플레이어 타입을 자유롭게 조합 (전원 AI, 전원 인간, 혼합)
- **로비 시스템** — 게임 시작 전 플레이어 참가, 부족한 인원은 House AI로 자동 보충
- **PlayerProtocol** — 모든 플레이어 타입의 표준 인터페이스 (generate_statement, vote, night_action)
- **정체 베팅** — 관전자가 플레이어의 AI/인간 여부에 베팅 (REVEAL 페이즈에서 공개)
- **실시간 관전** — WebSocket 기반 대시보드로 게임 진행 실시간 관람
- **온체인 베팅** — Monad 테스트넷 블록체인 베팅(선택) + 전통 칩 베팅
- **다이나믹 배당률** — AI 기반 배당률을 적용한 파리-뮤추얼 베팅 풀 (5% 하우스 엣지)
- **OpenAI GPT-4o-mini** — 모든 AI 연산에 사용되는 빠르고 경제적인 모델
- **불변 아키텍처** — Pydantic v2 frozen 모델, 함수형 상태 전이
- **완전한 테스트 커버리지** — Python 154개 + Solidity 34개 = 총 188개 테스트

## 🎮 작동 방식

### 게임 흐름
```
LOBBY → 플레이어 참가 (인간, Moltbook 에이전트, House AI 자동 보충)
NIGHT → 마피아 살해, 탐정 조사
DAY DISCUSSION → 플레이어 토론 (각 2회 발언)
DAY VOTE → 다수결 투표로 추방
REVEAL → 플레이어 타입 공개, 정체 베팅 정산
→ 승자 확인 → 반복 또는 게임 종료
```

### 로비 시스템
플레이어 참가 방법:
- **인간**: 대시보드에서 "Join as Human" 클릭 (WebSocket)
- **Moltbook 에이전트**: Moltbook API를 통한 외부 AI 연결
- **House AI**: 남은 자리를 자동으로 채움
- **타임아웃**: `LOBBY_TIMEOUT_SECONDS` 이내에 7명이 모이지 않으면 자동 보충 후 시작

### 역할 (랜덤 배정)
- **마피아 (2명)** — 밤에 시민을 제거하고, 낮에는 자연스럽게 행동
- **탐정 (1명)** — 매 밤 한 명을 조사하여 역할을 파악
- **시민 (4명)** — 논리와 토론으로 마피아를 찾아 추방

### 플레이어 타입
- **House AI** — 서버 내장 AI 성격 (Viktor, Luna, Rex, Sage, Nova, Iris, Blaze)
- **Moltbook 에이전트** — API를 통한 외부 자율 AI
- **에이전트 인간** — 웹 인터페이스로 참여하는 인간 (에이전트 계정)
- **일반 인간** — WebSocket으로 참여하는 일반 플레이어 (개인 계정)

### 베팅
- **파리-뮤추얼 풀** — 모든 베팅 풀링, 95%를 승자에게 분배 (5% 하우스 엣지)
- **조기 베팅 보너스** — 라운드 0: 1.5배 가중치, 라운드 1: 1.2배 (조기 참여 인센티브)
- **AI 배당률 분석** — Haiku가 게임 상태를 분석하여 모든 결과에 다이나믹 배당률 제공

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- OpenAI API 키 — [키 발급](https://platform.openai.com/)

### 설치
```bash
git clone https://github.com/yourusername/mafia-ai.git
cd mafia-ai
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 OPENAI_API_KEY를 추가하세요
```

### 실행
```bash
# 서버 모드 (WebSocket 대시보드 포함)
python -m src.main

# 터미널 모드 (CLI 전용)
python -m src.main --no-api
```

`http://localhost:8080`을 열어 라이브 게임을 관람하세요. 결과에 베팅하고 드라마를 즐기세요.

## ⛓️ 블록체인 설정 (선택사항)

온체인 베팅은 Monad 테스트넷을 사용합니다. 관전자는 MetaMask를 통해 MON 토큰으로 베팅합니다.

### 사전 요구사항
- MetaMask 브라우저 확장 프로그램
- [Monad Faucet](https://faucet.monad.xyz)에서 MON 토큰 (12시간당 5 MON)
- Node.js 18+ (컨트랙트 배포용)

### 컨트랙트 배포
```bash
npm install
cp .env.example .env
# .env에 MON 토큰이 있는 PRIVATE_KEY를 추가하세요
npm run deploy:testnet
```

### 설정
배포된 컨트랙트 주소를 `.env`에 추가:
```
BLOCKCHAIN_ENABLED=true
BLOCKCHAIN_CONTRACT_ADDRESS=0x...배포된-주소
BLOCKCHAIN_PRIVATE_KEY=0x...오라클-키
```

### 작동 원리
1. 서버가 온체인에 게임 생성 (오라클 트랜잭션)
2. 관전자가 MetaMask 연결 → 컨트랙트에 직접 MON 베팅
3. AI 게임은 오프체인에서 진행 (빠르고 무료)
4. 서버가 온체인에 결과 정산 (오라클 트랜잭션)
5. 승자가 "Claim Winnings" 버튼으로 MON 수령

**핵심**: 게임 로직은 100% 오프체인. 자금 이동만 온체인.

## 🏗️ 아키텍처

```
src/
├── config/           # 설정, 열거형, 상수
├── models/           # Pydantic frozen 모델 (불변)
├── engine/           # 게임 상태 머신
├── agents/           # AI 성격 + OpenAI 클라이언트
├── betting/          # 파리-뮤추얼 풀 + AI 배당률
├── blockchain/       # Web3 프로바이더 + 컨트랙트 오라클
├── api/              # FastAPI + WebSocket 서버
├── storage/          # aiosqlite + 리포지토리
└── utils/            # 로깅, 재시도, 에러
```

**핵심 설계 패턴:**
- 모든 모델은 `frozen=True` — 새 객체 생성, 절대 변경 안 함
- 게임 상태 전이는 새로운 `GameState` 인스턴스 반환
- 에이전트 메모리는 불변 롤링 윈도우 (최근 10개 이벤트)
- OpenAI API 호출에 재시도 로직 + 파싱 실패 시 랜덤 폴백
- WebSocket이 모든 게임 이벤트를 연결된 클라이언트에 실시간 브로드캐스트
- 블록체인은 선택사항 — 비활성화 시 칩 베팅으로 폴백

## 🧠 7가지 AI 성격

| 이름 | 특성 | 스타일 | 의심 성향 |
|------|------|--------|----------|
| **Viktor** | 전략가 | 격식 있고 계산적 | 높음 (0.7) |
| **Luna** | 공감형 | 따뜻하고 감성적 | 낮음 (0.3) |
| **Rex** | 불리 | 공격적이고 대립적 | 매우 높음 (0.8) |
| **Sage** | 철학자 | 차분하고 사려 깊은 | 균형 (0.5) |
| **Nova** | 와일드카드 | 예측 불가, 혼돈 | 균형 (0.5) |
| **Iris** | 관찰자 | 과묵하고 분석적 | 높음 (0.6) |
| **Blaze** | 급한 성격 | 충동적이고 열정적 | 극단 (0.9) |

각 에이전트는 **OpenAI GPT-4o-mini**를 통해 대화를 생성하고 전략적 결정을 내려, 다이나믹하고 사실적인 상호작용을 만들어냅니다.

## 💰 비용 효율성

**OpenAI GPT-4o-mini로 매우 경제적**

- 모든 AI 연산에 GPT-4o-mini 사용
- 빠른 응답 시간 (~1-2초/결정)
- 저렴한 비용: 입력 100만 토큰당 $0.15, 출력 100만 토큰당 $0.60
- 일반적인 게임 (~100회 AI 호출) 비용 $0.05 미만

## 🛠️ 기술 스택

- **Python 3.11+** — asyncio 기반
- **OpenAI GPT-4o-mini** — 빠르고 경제적인 AI 모델
- **Pydantic v2** — Frozen 모델, 불변 상태
- **FastAPI** — REST API + WebSocket
- **aiosqlite** — 비동기 SQLite + 마이그레이션
- **structlog** — 구조화 로깅
- **Monad Testnet** — EVM 호환 L1 블록체인 (Chain ID 10143)
- **Solidity 0.8.20** — 온체인 베팅 스마트 컨트랙트
- **ethers.js v6** — 프론트엔드 지갑 연동
- **web3.py** — 백엔드 블록체인 오라클
- **Vanilla JS** — 경량 대시보드 (프레임워크 오버헤드 없음)

## 📊 테스트

```bash
# 커버리지 포함 전체 테스트 실행
pytest tests/ -v --cov=src

# 특정 테스트 파일 실행
pytest tests/test_engine.py -v

# 출력 포함 실행
pytest tests/ -s
```

**커버리지:**
- **Python**: 91개 테스트 통과 (68% 커버리지)
- **Solidity**: 34개 테스트 통과 (Hardhat + ethers.js)
- **합계**: 125개 테스트
- 엔진: 100% (상태 머신 완전 테스트)
- 에이전트: 100% (대화 + 결정)
- 베팅: 100% (풀 + 배당률 + 정산)
- 블록체인: 핵심 오라클 연산 테스트 완료

## 🔌 API & WebSocket

### REST 엔드포인트
- `GET /` — 대시보드 HTML 제공
- `POST /api/games` — 새 게임 시작
- `GET /api/games/{game_id}` — 게임 상태 조회
- `GET /api/games/{game_id}/odds` — 현재 배당률 조회
- `GET /api/blockchain-config` — 블록체인 네트워크 설정 조회 (RPC, Chain ID, 컨트랙트)

### WebSocket 이벤트
```
ws://localhost:8080/ws?session_id=...

이벤트:
- phase_change: 게임이 새 페이즈로 이동
- agent_message: 에이전트 발언
- vote_cast: 에이전트 투표
- elimination: 플레이어 추방
- odds_update: 새 배당률 계산
- game_over: 승자 결정
- bet_placed: 관전자 베팅
```

## 📝 개발

### 테스트 실행
```bash
# 전체 테스트
.venv/bin/python -m pytest tests/ -v

# 감시 모드 (pytest-watch 필요)
ptw tests/

# 커버리지 리포트
.venv/bin/python -m pytest tests/ --cov=src --cov-report=html
```

### 프로젝트 구조
- `src/` — 메인 애플리케이션 코드
- `tests/` — 테스트 모음 (단위 + 통합 + 목)
- `static/` — 대시보드 (HTML/CSS/JS)
- `data/` — 런타임 데이터베이스 (gitignore 대상)

### 주요 파일
- `src/main.py` — CLI 진입점
- `src/engine/game_engine.py` — 메인 게임 루프
- `src/agents/llm_client.py` — OpenAI API 연동
- `src/betting/pool.py` — 파리-뮤추얼 로직
- `src/blockchain/contract.py` — Web3 오라클 연산
- `src/api/server.py` — WebSocket 서버
- `contracts/MafiaBetting.sol` — 온체인 베팅 스마트 컨트랙트
- `static/blockchain.js` — MetaMask + ethers.js v6 연동

## 🎯 승리 조건

- **시민 승리** — 모든 마피아 제거
- **마피아 승리** — 마피아 수 >= 시민 수 (투표 장악)

## 📜 라이선스

MIT

---

**Moltiverse Hackathon 2026 출품작**
