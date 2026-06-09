<div align="center">

# 돈다바짜

**청년 지원금 최적 조합 탐색기**

배타 제약 조건 기반 MWIS 알고리즘으로  
중복 없는 최대 수혜 조합을 자동 산출합니다

[![Frontend](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://oss-2026-10.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Railway-purple?logo=railway)](https://oss-2026-10-production.up.railway.app/)
[![API Docs](https://img.shields.io/badge/API-Swagger-green?logo=swagger)](https://oss-2026-10-production.up.railway.app/docs)

[**서비스 바로가기**](https://oss-2026-10.vercel.app/) · [**API 문서**](https://oss-2026-10-production.up.railway.app/docs) · [**검증 대시보드**](https://oss-2026-10-production.up.railway.app/dashboard)

</div>

---

## 문제 인식

청년 복지 정책에는 "A를 받으면 B를 받을 수 없다"는 배타 관계가 공고문 자연어 속에 흩어져 있습니다. 기존 서비스(복지로, 온통청년)는 조건 검색과 1회성 매칭만 제공하며, 정책 간 배타 관계를 고려한 최적 조합 계산 기능이 없습니다.

**돈다바짜는 이 문제를 MWIS(Maximum Weight Independent Set) 문제로 모델링하여 수학적으로 최적인 수혜 조합을 0.3초 안에 산출합니다.**

---

## 핵심 기능

- **최적 조합 탐색** — 배타 제약을 자동으로 처리하고 수혜액 합산이 최대인 정책 조합 산출
- **환승 로드맵** — MWIS 결과 이후 DAG DP로 5년 수혜 타임라인 자동 생성
- **배타 그래프 시각화** — ReactFlow / D3 포스 그래프로 정책 간 관계 인터랙티브 탐색
- **알고리즘 검증 대시보드** — 5개 솔버 교차검증 + 전수열거 산점도 실시간 확인

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| Frontend | React, ReactFlow, D3.js, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL (Supabase) |
| 알고리즘 | MWIS 5종 솔버, DAG DP |
| 배포 | Vercel (프론트), Railway (백엔드) |

---

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- Supabase 프로젝트 (또는 로컬 PostgreSQL)

### 백엔드

```bash
git clone https://github.com/ji2081/OSS-2026-10.git
cd OSS-2026-10/backend

python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Mac/Linux

pip install -r requirements.txt
uvicorn main:app --reload
```

### 프론트엔드

```bash
cd ../frontend
npm install
npm run dev
```

### 환경 변수

프로젝트 루트에 `.env` 파일 생성:

```env
DB_DSN=postgresql+asyncpg://<user>:<password>@<host>/<db>
SUPABASE_JWT_SECRET=<your_jwt_secret>
LLM_API_KEY=<claude_api_key>
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 알고리즘

본 프로젝트의 핵심은 MWIS 5종 솔버와 DAG DP 환승 로드맵입니다.

```
Stage A  BruteForce          2^N 전수탐색 (검증 기준값)
Stage B  DFS + 가지치기      상한선 가지치기 + 상태 캐싱 (production)
Stage C1 Branch and Bound    분기한정법
Stage C2 Preprocess          고립 노드 분리 전처리 → O(2^K), K << N
Stage C3 Complement Clique   여그래프 변환 → MWIS ↔ MWC 동치 증명
```

알고리즘 상세 설명 → [`ALGORITHM.md`](./ALGORITHM.md)

---

## 알고리즘 검증

| 검증 방법 | 결과 | 입증 |
|---|---|---|
| 5개 솔버 교차검증 (4 프로필 × 5 솔버 = 20회) | 불일치 0건 | Stage B가 수학적 최적해 반환 |
| 유효 조합 전수 열거 (산점도) | MWIS = 전체 1위 (평균 대비 1.96배) | 가능한 모든 조합 중 최대값 확인 |
| Stage B 수학적 정확성 증명 | 완전성·가지치기 안전성·캐시 정확성 증명 | 어떤 입력에도 최적 보장 |

**검증 대시보드:** https://oss-2026-10-production.up.railway.app/dashboard

---

## API

**Swagger UI:** https://oss-2026-10-production.up.railway.app/docs

| Method | Endpoint | 설명 |
|---|---|---|
| POST | `/policies/optimize` | MWIS 최적 조합 탐색 |
| POST | `/policies/roadmap` | DAG DP 환승 로드맵 생성 |
| GET | `/verify/cross-solver` | 5개 솔버 교차 검증 |
| GET | `/verify/distribution` | 유효 조합 전수 열거 산점도 |
| GET | `/results/latest` | 최근 최적화 결과 조회 |
| GET | `/health` | 서버·DB 상태 확인 |

---

## 프로젝트 구조

```
OSS-2026-10/
├── backend/
│   ├── main.py
│   ├── verify.html                      # 검증 대시보드
│   ├── routers/
│   │   ├── policy_router.py             # optimize
│   │   ├── roadmap_router.py            # roadmap (DAG DP)
│   │   ├── result_router.py
│   │   └── verification_router.py
│   └── services/
│       ├── mwis/
│       │   ├── base_solver.py           # 전략 패턴 추상 클래스
│       │   ├── graph_builder.py
│       │   └── solvers/                 # Stage A·B·C1·C2·C3
│       └── transition/
│           └── roadmap_planner.py       # DAG DP 2단 파이프라인
└── frontend/
    └── src/pages/
        ├── DashboardPage.jsx
        ├── RoadmapPage.jsx
        ├── GraphPage.jsx                # ReactFlow
        └── ExclusionGraphPage.jsx       # D3
```

---

## 팀

2026 공개SW 02분반 10조

---

## License

MIT