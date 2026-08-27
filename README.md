<div align="center">

<img src="frontend/src/logo.png" alt="돈다바짜" width="88" />

# 돈다바짜

**청년 지원금 최적 조합 탐색기**

"A를 받으면 B는 못 받는다"는 배타 조건을 자동으로 계산해  
받을 수 있는 지원금 조합 중 수혜액이 가장 큰 조합을 찾아줍니다

[![Frontend](https://img.shields.io/badge/Frontend-Vercel-black?logo=vercel)](https://dabazza.vercel.app/)
[![Backend](https://img.shields.io/badge/Backend-Railway-purple?logo=railway)](https://oss-2026-10-production.up.railway.app/)
[![API Docs](https://img.shields.io/badge/API-Swagger-85EA2D?logo=swagger&logoColor=black)](https://oss-2026-10-production.up.railway.app/docs)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)

[**서비스 바로가기**](https://dabazza.vercel.app/) · [**API 문서**](https://oss-2026-10-production.up.railway.app/docs) · [**검증 대시보드**](https://oss-2026-10-production.up.railway.app/dashboard)

</div>

---

## 목차

- [해결하려는 문제](#해결하려는-문제)
- [데모](#데모)
- [주요 기능](#주요-기능)
- [동작 방식](#동작-방식)
- [시작하기](#시작하기)
- [테스트](#테스트)
- [알고리즘](#알고리즘)
- [알고리즘 검증](#알고리즘-검증)
- [API](#api)
- [데이터](#데이터)
- [프로젝트 구조](#프로젝트-구조)
- [AI 활용 범위](#ai-활용-범위)
- [확장 방향](#확장-방향)
- [참고 문헌](#참고-문헌)
- [팀](#팀)
- [라이선스](#라이선스)

---

## 해결하려는 문제

청년 지원 정책에는 "A를 받으면 B는 받을 수 없다"는 **배타 관계**가 공고문 자연어 속에 흩어져 있습니다. 게다가 배타 관계라도 수혜 기간이 겹치지 않으면 순차적으로 둘 다 받을 수 있어, 개인이 최적 조합을 손으로 계산하기는 사실상 불가능합니다.

기존 서비스(복지로, 온통청년)는 **조건 검색과 1회성 매칭만** 제공합니다.

| 기능 | 복지로 · 온통청년 | 돈다바짜 |
|---|:---:|:---:|
| 조건 검색 | ✅ | ✅ |
| 배타 관계 자동 계산 | ❌ | ✅ |
| 최적 조합 산출 | ❌ | ✅ |
| 시계열 환승 로드맵 | ❌ | ✅ |

정책 목록과 기본 메타데이터는 공공 API로 확보할 수 있지만, **MWIS 연산에 필요한 배타 관계와 수혜액 산정 규칙은 어떤 공개 API도 제공하지 않습니다.** 이 프로젝트의 기여는 그 관계를 구조화한 데이터셋과, 그 위에서 최적 조합을 계산하는 엔진에 있습니다.

---

## 데모

> 아래 이미지 경로에 스크린샷을 넣어주세요. (`docs/images/` 폴더 생성 후 저장)

| 대시보드 | 배타 관계 그래프 |
|---|---|
| ![대시보드](docs/images/dashboard.png) | ![배타 그래프](docs/images/graph.png) |

| 수혜 로드맵 | 검증 대시보드 |
|---|---|
| ![로드맵](docs/images/roadmap.png) | ![검증](docs/images/verify.png) |

**시연 영상**: <!-- 유튜브 링크를 넣어주세요 -->

---

## 주요 기능

- **최적 조합 탐색** — 배타 제약을 자동으로 처리하고 수혜액 합산이 최대인 조합 산출
- **환승 로드맵** — 한 정책이 끝난 뒤 이어받을 수 있는 경로를 DAG DP로 계산해 간트차트로 표시
- **배타 관계 그래프** — ReactFlow와 D3 포스 그래프로 정책 간 충돌 관계를 인터랙티브하게 탐색
- **알짜배기 정보** — 현금성 외 바우처·할인·현물 혜택을 별도 레이어로 제공
- **알고리즘 검증 대시보드** — 5개 솔버 교차검증과 전수 열거 산점도를 실시간 확인
- **모바일 반응형** — 좁은 화면에서도 대시보드와 로드맵 탐색 지원

---

## 동작 방식

```
프로필 입력            정책 필터링           그래프 구성            최적화              결과 시각화
나이·소득·지역   →   policy_filter.py  →  graph_builder.py  →  MWIS 솔버      →   대시보드
취업 여부            조건 부합 정책만      노드=정책             (Stage B)          간트 로드맵
                                          간선=배타 관계                            배타 그래프
                                          가중치=수혜액
```

| 단계 | 모듈 | 하는 일 |
|---|---|---|
| 1 | `policy_filter.py` | 나이·소득·지역·취업 여부로 후보 정책 선별 |
| 2 | `graph_builder.py` | 배타 관계를 무방향 그래프로 구성, 정합성 결함 자동 보정 |
| 3 | `solvers/stage_b_dp.py` | 최대 가중치 독립집합 탐색 |
| 4 | `roadmap_planner.py` | 선택된 조합 이후의 환승 경로를 DAG DP로 계산 |

`graph_builder.py`는 데이터 정합성을 전담하고, 솔버는 수학적 최적화만 담당합니다. 이 책임 분리 덕분에 각 계층을 독립적으로 검증할 수 있습니다.

---

## 시작하기

### 요구사항

| 항목 | 버전 |
|---|---|
| Python | 3.11 이상 |
| Node.js | 18 이상 |
| PostgreSQL | Supabase 프로젝트 또는 로컬 인스턴스 |

### 설치 및 실행

```bash
git clone https://github.com/ji2081/OSS-2026-10.git
cd OSS-2026-10
```

**백엔드**

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
uvicorn main:app --reload      # http://127.0.0.1:8000
```

**프론트엔드**

```bash
cd frontend
npm install
npm start                      # http://localhost:3000
```

**Docker로 백엔드 실행**

```bash
cd backend
docker build -t dabazza-backend .
docker run -p 8000:8000 --env-file ../.env dabazza-backend
```

### 환경 변수

프로젝트 루트에 `.env` 를 만듭니다. 백엔드는 **동기 드라이버(psycopg2)** 를 사용하므로 DSN 스킴에 주의하세요.

| 변수 | 필수 | 설명 |
|---|:---:|---|
| `DB_DSN` | ✅ | `postgresql+psycopg2://user:password@host:port/db` |
| `SUPABASE_JWT_SECRET` | ✅ | Supabase Auth JWT 검증용 시크릿 |
| `ALLOWED_ORIGINS` | | CORS 허용 origin, 쉼표 구분 (기본값 `http://localhost:3000,http://localhost:5173`) |

프론트엔드는 `frontend/.env` 에 별도로 설정합니다.

| 변수 | 필수 | 설명 |
|---|:---:|---|
| `REACT_APP_API_URL` | ✅ | 백엔드 주소 (예: `http://127.0.0.1:8000`) |
| `REACT_APP_SUPABASE_URL` | ✅ | Supabase 프로젝트 URL |
| `REACT_APP_SUPABASE_ANON_KEY` | ✅ | Supabase anon key |

> CRA는 빌드 시점에 환경 변수를 주입하므로, 값을 바꾸면 재빌드가 필요합니다.

---

## 테스트

```bash
cd backend
pytest services/mwis/ -v
```

MWIS 그래프 구성과 수혜 기간 산정에 대한 단위 테스트가 실행됩니다. 정상 케이스보다 **더러운 입력**(단방향 배타 누락, self-loop, 존재하지 않는 UUID 참조, 기간 경계값)에 검증을 집중했습니다.

---

## 알고리즘

정책을 노드, 배타 관계를 간선, 수혜액을 가중치로 두면 이 문제는 **최대 가중치 독립집합(MWIS)** 문제가 됩니다.

```
maximize   Σ w(v) · x(v)
subject to x(u) + x(v) ≤ 1    ∀(u, v) ∈ E
           x(v) ∈ {0, 1}
```

MWIS는 NP-hard이지만, 프로필 필터링 후 후보 수가 10~15 수준이므로 도메인 특화 가지치기로 **정확해**를 실시간에 반환할 수 있습니다.

| 단계 | 구현 | 핵심 아이디어 | 역할 | N=12 실측 |
|---|---|---|---|---|
| Stage A | `stage_a_naive.py` | 2^N 전수탐색 | 검증 기준값 (Oracle) | 13.54ms |
| **Stage B** | `stage_b_dp.py` | 상한선 가지치기 + 탐색 상태 캐시 | **운영 솔버** | **0.29ms** |
| Stage C1 | `stage_c_1_bnb.py` | LP 완화 기반 분기한정 | 독립 검증 | 1.86ms |
| Stage C2 | `stage_c_2_preprocess.py` | 고립 노드 분리 → O(2^K), K ≪ N | 독립 검증 | 0.15ms |
| Stage C3 | `stage_c_3_clique.py` | 여그래프 변환, MWIS(G) = MWC(Ḡ) | 독립 검증 | 0.45ms |

> 탐색 공간 2¹² = 4,096인 프로필 기준 실측입니다. 전수탐색 대비 운영 솔버는 약 47배 빠릅니다.

**운영에 쓰는 솔버는 Stage B 하나뿐입니다.** 나머지 넷은 그 결과가 최적임을 외부에서 증명하기 위한 독립 구현으로, 서로 다른 알고리즘 패러다임을 사용합니다.

상세 설명 → [`ALGORITHM.md`](./ALGORITHM.md)

---

## 알고리즘 검증

최적화 알고리즘은 "정답을 모르는 상태에서 정답을 냈는지" 확인해야 하므로, 자기 자신을 근거로 삼을 수 없습니다. 그래서 세 층의 외부 검증을 두었습니다.

| 검증 | 방법 | 증명하는 것 | 결과 |
|---|---|---|---|
| 교차 검증 | 5개 솔버가 동일 입력을 풀어 Stage A와 비교 | 구현이 정확한가 | 20회 비교, 불일치 0건 |
| 분포 검증 | 가능한 모든 유효 조합을 열거해 순위 확인 | 그 답이 정말 최대인가 | 55개 중 1위, 평균 대비 1.99배 |
| 전수 검증 | 연령×소득×지역×취업여부 조합 전체 자동 검증 | 특정 케이스에만 맞는 게 아닌가 | 독립집합 제약 위반 0건 |

분포 검증 기준 프로필(25세·미취업·서울·소득 60%)에서 후보 정책 7개로 만들 수 있는
유효 조합은 55개이며, 평균 수혜액 464만원·중앙값 457만원에 대해 MWIS 최적값은 **925만원**입니다.

결과는 [검증 대시보드](https://oss-2026-10-production.up.railway.app/dashboard)에서 실시간으로 확인할 수 있습니다.

---

## API

**Swagger UI**: https://oss-2026-10-production.up.railway.app/docs

| Method | Endpoint | 설명 |
|---|---|---|
| `POST` | `/policies/optimize` | 프로필 기반 MWIS 최적 조합 탐색 |
| `POST` | `/policies/roadmap` | DAG DP 환승 로드맵 생성 |
| `GET` | `/verify/cross-solver` | 5개 솔버 교차 검증 |
| `GET` | `/verify/distribution` | 유효 조합 전수 열거 산점도 |
| `GET` | `/verify/exhaustive` | 프로필 조합 전수 자동 검증 |
| `GET` | `/results/latest` | 최근 최적화 결과 조회 |
| `GET` | `/health` | 서버·DB 상태 확인 |
| `GET` | `/dashboard` | 알고리즘 검증 대시보드 |

사용자 프로필 관련 엔드포인트를 포함한 전체 명세는 `/docs` 를 참고하세요.

---

## 데이터

| 항목 | 수량 |
|---|---|
| 구축 정책 | 130건 (활성 115건) |
| MWIS 후보 (`is_supplementary=false`) | 15개 |
| 보조·알짜배기 레이어 | 100개 |
| 배타 간선 | 41개 |

정책 데이터는 공고 원문을 확인해 수동 검증한 뒤 적재합니다. 배타 관계 오류 하나가 최적해 전체를 오염시키므로, 자동 적재보다 정확성을 우선했습니다.

주요 스키마는 `policies`(정책 메타데이터와 배타 관계), `policy_tiers`(소득 구간별 수혜액·기간)입니다.

---

## 프로젝트 구조

```
OSS-2026-10/
├── backend/
│   ├── main.py                      # FastAPI 진입점, CORS·헬스체크
│   ├── database.py                  # 동기 엔진, PgBouncer 대응 풀 설정
│   ├── Dockerfile
│   ├── verify.html                  # 검증 대시보드
│   ├── models/ schemas/ routers/    # ORM · Pydantic · 엔드포인트
│   └── services/
│       ├── mwis/
│       │   ├── base_solver.py       # 솔버 추상 인터페이스 (전략 패턴)
│       │   ├── graph_builder.py     # 배타 그래프 구성 및 정합성 보정
│       │   ├── tier_resolver.py     # 소득 구간별 tier 결정
│       │   ├── benchmark.py         # 솔버 성능 비교
│       │   └── solvers/             # Stage A · B · C1 · C2 · C3
│       └── transition/
│           └── roadmap_planner.py   # DAG DP 환승 로드맵
├── etl/                             # 오프라인 데이터 구축 (서비스 런타임과 분리)
│   ├── extract/ transform/ validate/ load/
│   ├── run.py                       # 수집 → 정형화 → staging
│   └── promote.py                   # 검토 완료분 승격
└── frontend/
    └── src/
        ├── pages/                   # Dashboard · Roadmap · Graph · ExclusionGraph
        ├── components/
        └── lib/
```

---

## AI 활용 범위

**서비스 실행 경로에는 AI 모델이 탑재되어 있지 않습니다.** 사용자 요청에 대한 최적 조합 계산은 전적으로 결정론적 MWIS 알고리즘으로 수행됩니다.

정책 데이터를 구축하는 [`etl/`](./etl/README.md) 파이프라인은 비정형 공고문을 구조화 JSON으로 변환하는 단계에서 상용 LLM API를 사용합니다. 이는 개발자가 수동으로 실행하는 **오프라인 도구**이며, 결과는 staging 단계의 사람 검토를 거쳐 반영됩니다. 배타 관계 매핑과 MWIS 후보 판정은 자동화하지 않고 공고 원문 대조로 확정합니다.

개발 과정에서 코드 작성·디버깅 보조용으로 상용 AI 서비스를 활용했습니다.

---

## 확장 방향

현재는 서울 거주 청년을 기준으로 데이터를 구축했습니다. MWIS 엔진 자체는 도메인에 종속되지 않으므로 다음과 같이 확장할 수 있습니다.

- **지역 확대** — 동일한 스키마로 전국 지자체 정책까지 수집 범위 확장
- **최적 조합 설명** — 특정 정책이 선택되거나 제외된 이유를 근거와 함께 제시
- **조건 시뮬레이션** — 특정 정책을 강제로 포함·제외했을 때의 수혜액 비교
- **타 도메인 적용** — 보험 상품 조합, 수강 신청 등 배타 조건이 존재하는 문제로 엔진 이식

---

## 참고 문헌

1. Karp, R. M. (1972). *Reducibility Among Combinatorial Problems*. Complexity of Computer Computations, 85–103.
2. Nemhauser, G. L., & Trotter, L. E. (1975). *Vertex Packings: Structural Properties and Algorithms*. Mathematical Programming, 8(1), 232–248.
3. Tomita, E., & Seki, T. (2003). *An Efficient Branch-and-Bound Algorithm for Finding a Maximum Clique*. DMTCS.

---

## 팀

**Vertex** — 2026 공개SW 프로젝트 02분반 10조

| 이름 | 담당 |
|---|---|
| 정지민 | Backend · MWIS 알고리즘 · 검증 시스템 |
| 황준호 | Backend · ETL 파이프라인 · 데이터 품질 |
| 이기현 | Frontend · 대시보드 · 배타 그래프 |
| 김세윤 | Frontend · 인증 · 로드맵 · 반응형 |

---

## 라이선스

이 프로젝트는 [MIT License](./LICENSE)를 따릅니다.

사용한 오픈소스 라이브러리와 각 라이선스는 [`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md)에 정리되어 있습니다.
