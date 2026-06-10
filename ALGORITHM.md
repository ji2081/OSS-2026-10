# 돈다바짜 — 청년 지원금 최적 조합 탐색기

> 상호 배타적 제약 조건 기반 MWIS 알고리즘으로 청년 복지 정책의 최적 수혜 조합을 자동 산출합니다.

2026 공개SW 02분반 10조

---

## 프로젝트 개요

청년 복지 정책들 사이에는 "A를 받으면 B를 받을 수 없다"는 배타 관계가 공고문 자연어 속에 산재해 있습니다. 기존 서비스(복지로, 온통청년)는 조건 조회 및 1회성 매칭만 제공하며, 정책 간 중복 제한 계산 기능이 없습니다.

본 프로젝트는 이 문제를 **최대 가중치 독립 집합(MWIS, Maximum Weight Independent Set)** 문제로 모델링하여 배타 제약을 만족하는 최적 정책 조합을 자동으로 산출합니다.

```
정책 노드 + 배타 간선 그래프
→ MWIS 탐색 (수혜액 합산 최대 독립집합)
→ 최적 조합 + DAG DP 환승 로드맵 반환
```

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | React, ReactFlow, D3.js, Tailwind CSS, Vercel |
| Backend | FastAPI, SQLAlchemy 2.0, Python |
| Database | PostgreSQL (Supabase 호스팅) |
| Auth | Supabase Auth |

---

## 알고리즘

### MWIS 문제 정의

```
max Σ w(v)·x(v)
subject to  x(u) + x(v) ≤ 1  ∀(u,v) ∈ E
            x(v) ∈ {0, 1}
```

정책 = 노드, 배타 관계 = 간선, 수혜액 = 가중치. 간선으로 연결된 노드를 동시에 선택하지 않으면서 가중치 합을 최대화하는 독립집합을 탐색합니다.

### 5종 솔버 — 발전 과정

#### Stage A — BruteForceSolver (`stage_a_naive.py`)

멱집합(Power Set) 전수탐색. 2^N개 모든 부분집합을 열거하고 독립집합 여부를 확인합니다.

- 시간복잡도: O(2^N)
- 역할: 수학적으로 최적이 보장되는 **교차검증 기준값(Oracle)**
- 한계: N이 커질수록 기하급수적으로 느려져 실서비스 적용 불가

**→ A의 한계에서 B가 탄생:**
전수탐색을 관찰하니 두 가지 낭비가 있었습니다. ① 현재까지 찾은 최적보다 더 나은 답이 나올 수 없는 분기를 계속 탐색. ② 같은 탐색 상태에서 시작점만 더 나쁜 경로를 반복 탐색.

---

#### Stage B — DPDFSSolver (`stage_b_dp.py`)

DFS 백트래킹 + 상한선 가지치기 + 탐색 상태 중복 제거.

```python
# 상한선 가지치기
upper_bound = current_value + sum(weights[i] for i not in excluded)
if upper_bound <= best["value"]:
    return  # 더 나은 답 불가능 → 조기 종료

# 탐색 상태 중복 제거
state = (idx, frozenset(excluded))
if state in memo and memo[state] >= current_value:
    return  # 이 상태에서 더 좋은 경로 이미 탐색 → 스킵
memo[state] = current_value
```

- 시간복잡도: worst case O(2^N), 평균적으로 대폭 감소
- **현재 production 솔버**
- 주의: `memo`는 전통적 DP 테이블(최적값 조회·재사용)이 아니라, 탐색 상태 캐시(중복 경로 제거)입니다.

**→ B의 한계에서 C2가 탄생:**
B는 배타 관계가 없는 노드도 DFS로 탐색합니다. 배타 관계 없는 노드는 항상 선택하면 됨이 자명한데 불필요한 탐색을 수행하고 있었습니다.

---

#### Stage C1 — BranchAndBoundSolver (`stage_c_1_bnb.py`)

분기한정법. Stage B보다 타이트한 상한선 추정으로 더 공격적으로 가지치기합니다.

---

#### Stage C2 — PreprocessSolver (`stage_c_2_preprocess.py`)

고립 노드 분리 전처리 + DFS 백트래킹.

```python
# 1단계: 배타 관계 없는 노드(고립 노드) 분리 → 무조건 전부 선택
isolated = [n for n, nbrs in adjacency.items() if not nbrs]

# 2단계: 배타 관계 있는 노드 K개만 DFS 탐색
connected = [n for n, nbrs in adjacency.items() if nbrs]
```

- 시간복잡도: O(2^K), K = 배타 관계 있는 노드 수 (K << N)
- 도메인 인사이트: "배타 관계 없는 정책은 항상 선택하면 된다"

---

#### Stage C3 — ComplementGraphCliqueSolver (`stage_c_3_clique.py`)

여그래프 변환 후 최대 가중치 클리크(MWC) 탐색.

**수학적 동치 증명:**
```
S ⊆ V 가 G의 독립집합  ⟺  S가 Ḡ(여그래프)의 클리크
따라서: MWIS(G) = MWC(Ḡ)
```

가중 채색 상한선(Weighted Greedy Coloring UB) + 접미사 합 가지치기 결합.
G가 Dense(배타 관계 많음)할수록 Ḡ가 Sparse → 클리크 탐색이 빠름.

> 참고: Tomita, E. & Seki, T. (2003), DMTCS.

---

### DAG DP 환승 로드맵 (`roadmap_planner.py`)

MWIS로 공간 최적화 후 시간 축으로 추가 최적화합니다.

```
Phase 1: MWIS 결과 정책들의 수혜 타임라인 구성
         (benefit_start, benefit_end 계산)

Phase 2: Phase 1 종료 후 시작 가능한 정책들로
         DAG DP 실행 → 최적 환승 경로 탐색

transitions: Phase 1 마지막 정책 → Phase 2 첫 정책 → ...
```

---

## 알고리즘 검증

### 1. 교차 솔버 검증 (`/verify/cross-solver`)

동일 입력에 대해 5개 솔버를 동시 실행하여 결과를 비교합니다.

- 4개 프로필 × 5개 솔버 = 20회 비교, **불일치 0건**
- 입증: "서로 다른 5가지 방법으로 풀어도 전부 같은 답 = Stage B가 최적해를 반환함"

### 2. 유효 조합 전수 열거 (`/verify/distribution`)

N개 후보 정책의 모든 유효 독립집합을 직접 열거하고 수혜액 분포를 산점도로 시각화합니다.

- 25세/서울/미취업/소득60% 기준: 27개 유효 조합 중 **MWIS = 전체 1위(672만원)**
- 평균 수혜액(342만원) 대비 **1.96배**
- 입증: "가능한 모든 유효 조합 중 MWIS 결과가 최대값"

### 3. Stage B 수학적 정확성 증명

완전성 · 가지치기 안전성 · 탐색 상태 캐시 정확성 세 가지 명제를 수학적으로 증명합니다.
→ 입증: "4개 테스트 프로필이 아닌, 어떤 입력에 대해서도 최적 보장"

검증 대시보드: `GET /dashboard`

---

## 데이터 파이프라인

```
Extract   온통청년 API(433개) + 복지로 내부 API(1,530개)
          = 최대 1,963개 비정형 공고문 원문 수집

Transform LLM(Claude API) 기반 자연어 → 구조화 JSON 정규화
          Pydantic 스키마 검증 (타입 불일치·필드 누락 차단)
          confidence 점수 자동 산출

Validate  confidence ≥ 0.5 임계값 필터링
          미달 항목은 etl_logs 테이블에 기록

Load      PostgreSQL upsert (ON CONFLICT)
```

ETL 실행 후 수동 정제: exclusive_with UUID 양방향 보정, is_supplementary 분류 검토, benefit_type 재분류.

**현재 DB**: 활성 정책 112개 (MWIS 후보 11개, 보조정책 101개)

---

## 프로젝트 구조

```
OSS-2026-10/
├── backend/
│   ├── main.py                         # FastAPI 앱 진입점
│   ├── verify.html                     # 검증 대시보드 UI
│   ├── routers/
│   │   ├── policy_router.py            # /policies/optimize
│   │   ├── roadmap_router.py           # /policies/roadmap
│   │   ├── result_router.py            # /results/latest
│   │   ├── user_router.py              # 사용자 인증
│   │   └── verification_router.py     # /verify/*
│   ├── services/
│   │   ├── mwis/
│   │   │   ├── base_solver.py          # 전략 패턴 추상 클래스
│   │   │   ├── graph_builder.py        # 배타 그래프 + 가중치 계산
│   │   │   ├── benchmark.py            # 솔버 성능 비교
│   │   │   └── solvers/
│   │   │       ├── stage_a_naive.py    # BruteForceSolver
│   │   │       ├── stage_b_dp.py       # DPDFSSolver (production)
│   │   │       ├── stage_c_1_bnb.py    # BranchAndBoundSolver
│   │   │       ├── stage_c_2_preprocess.py  # PreprocessSolver
│   │   │       └── stage_c_3_clique.py # ComplementGraphCliqueSolver
│   │   ├── transition/
│   │   │   └── roadmap_planner.py      # DAG DP 2단 파이프라인
│   │   └── policy_filter.py            # 프로필 기반 정책 필터링
│   ├── models/                         # SQLAlchemy 모델
│   └── schemas/                        # Pydantic 스키마
└── frontend/
    └── src/
        └── pages/
            ├── DashboardPage.jsx       # 메인 대시보드
            ├── RoadmapPage.jsx         # 간트 차트 로드맵
            ├── GraphPage.jsx           # ReactFlow 배타 그래프
            ├── ExclusionGraphPage.jsx  # D3 포스 그래프
            └── BenefitsPage.jsx        # 보조정책 정보
```

---

## 실행 방법

### 환경 변수

프로젝트 루트 `.env` 파일:

```env
DB_DSN=postgresql+asyncpg://...   # Supabase Transaction Pooler URL
SUPABASE_JWT_SECRET=...
LLM_API_KEY=...
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 백엔드

```bash
cd backend
python -m venv venv
source venv/Scripts/activate    # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

### 검증 대시보드

백엔드 실행 후 `http://localhost:8000/dashboard`

### 솔버 벤치마크

```bash
cd backend
source venv/Scripts/activate
python -m services.mwis.benchmark
```

---

## API 주요 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| POST | `/policies/optimize` | MWIS 최적 조합 탐색 |
| POST | `/policies/roadmap` | DAG DP 환승 로드맵 |
| GET | `/verify/cross-solver` | 5개 솔버 교차 검증 |
| GET | `/verify/distribution` | 유효 조합 전수 열거 산점도 |
| GET | `/results/latest` | 최근 최적화 결과 조회 |
| GET | `/dashboard` | 검증 대시보드 |
| GET | `/health` | 서버·DB 상태 확인 |

---

## DB 스키마 핵심

### policies

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR | 정책명 |
| benefit_type | VARCHAR | subsidy/savings/voucher/loan 등 |
| is_supplementary | BOOLEAN | false=MWIS 후보, true=보조 레이어 |
| exclusive_with | JSONB | 배타 정책 UUID 배열 (양방향 보정 완료) |
| income_threshold | FLOAT8 | 소득 기준 (중위소득 비율) |
| super_region | VARCHAR | 지역 (서울/전국 등) |

### policy_tiers

| 컬럼 | 타입 | 설명 |
|---|---|---|
| policy_id | UUID | FK → policies.id |
| max_income_ratio | FLOAT8 | 소득 구간 상한 |
| monthly_benefit | BIGINT | 월 수혜액 (원) |
| duration_months | INTEGER | 수혜 기간 (개월) |

---

## 개발 환경

- OS: Windows + Git Bash
- Python: 3.11+
- Node.js: 18+
- DB: Supabase (PostgreSQL 15)
- 배포: Vercel (프론트) + 백엔드 서버