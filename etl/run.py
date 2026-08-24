import os
import re
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from etl.extract.api_extractor import extract_policies_as_list, RawApiPolicy
from etl.extract.llm_extractor import crawl_bokjiro, RawCrawledPolicy
from etl.transform.llm_normalizer import normalize_batch
from etl.load.db_inserter import insert_batch
from etl.validate.schema import PolicySchema

LLM_API_KEY: str = os.environ["LLM_API_KEY"]
DB_DSN: str = os.environ.get(
    "DB_DSN",
    "postgresql://policy_admin:password@localhost:5432/youth_policy",
)
CONFIDENCE_THRESHOLD = 0.5
CACHE_PATH = "etl_cache.json"

EXCLUDE_KEYWORDS = [
    "인턴", "봉사", "캠프", "페스티벌", "공모전", "경진대회",
    "해외", "교류", "기자단", "서포터즈", "홍보대사",
    "아카데미", "스쿨", "강좌", "교육과정",
    "연수", "훈련", "양성", "육성", "인재",
    "R&D", "연구", "실험",
    "경남", "경북", "강원", "전남", "전북", "충남", "충북",
    "부산", "대구", "인천", "광주", "대전", "울산",
    "세종", "제주", "새만금", "광양", "의성",
    "재직자", "귀농", "귀촌", "군인", "병사",
    "사관학교", "외국인", "어르신", "노년", "중장년",
    "초등", "중학", "고등", "대학원", "박사",
    "공간운영", "센터운영", "행사", "대회",
]


def _is_relevant(name: str) -> bool:
    return not any(kw in name for kw in EXCLUDE_KEYWORDS)


def _normalize_title(name: str) -> str:
    return re.sub(r'\s+', ' ', name).strip()


def _api_policies_to_raw(items: list[RawApiPolicy]) -> list[tuple[str, str, str, str]]:
    # 검색 API가 이미 숫자/날짜로 주는 값(EARN_MIN_AMT, APLY_PRD_BGNG_YMD 등)을
    # 예전엔 버렸었는데, 이제 텍스트에 명시적으로 실어 보낸다 — LLM이 "본문에
    # 안 적힌 값"을 잘못 추측할 필요 없이 API가 준 값을 그대로 옮겨쓰기만 하면
    # 되므로 정확도가 올라간다.
    # 마지막 값(atch_file_mng_sn)은 LLM 프롬프트에 넣지 않는다 — 이건 llm_normalizer의
    # PDF 승격 단계가 필요할 때만 쓰는 내부 참조 ID다.
    return [
        (
            f"정책명: {p.name}\n주관기관: {p.host_org}\n대상지역: {p.target_region}\n"
            f"신청기간(원문): {p.apply_period} ({p.apply_start_ymd}~{p.apply_end_ymd})\n"
            f"소득기준(API 원값): 하한 {p.income_min_amt or '없음'} / 상한 {p.income_max_amt or '없음'}\n"
            f"대상나이: {p.age_min}~{p.age_max}세\n"
            f"개요: {p.overview}\n지원내용: {p.support_content}\n"
            f"추가 자격조건: {p.add_qualification or '없음'}\n"
            f"신청방법: {p.apply_method or '없음'}",
            p.source_url,
            _normalize_title(p.name),
            p.atch_file_mng_sn,
        )
        for p in items
    ]


def _crawled_to_raw(items: list[RawCrawledPolicy]) -> list[tuple[str, str, str, str]]:
    # 복지로는 첨부파일 다운로드 경로를 아직 리버스엔지니어링하지 않아서
    # atch_file_mng_sn 자리에 빈 문자열을 넣는다 — PDF 승격은 자동으로 스킵됨.
    return [(it.raw_text, it.url, _normalize_title(it.name), "") for it in items]


def _save_cache(schemas: list) -> None:
    cache_data = []
    for s in schemas:
        if s is not None and not isinstance(s, Exception):
            cache_data.append(s.model_dump(mode='json'))
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, default=str)
    print(f"  → 정형화 결과 저장: {CACHE_PATH} ({len(cache_data)}개)")


def _load_cache() -> list[PolicySchema] | None:
    if not os.path.exists(CACHE_PATH):
        return None
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    schemas = []
    for item in data:
        try:
            schemas.append(PolicySchema(**item))
        except Exception:
            pass
    print(f"  → 캐시에서 로드: {len(schemas)}개")
    return schemas


async def run_pipeline(use_cache: bool = False, limit: int | None = None) -> None:
    print("=" * 60)
    print("청년 지원금 ETL 파이프라인 시작")
    print("=" * 60)

    schemas: list[PolicySchema | None] = []

    if use_cache:
        print("\n[캐시 모드] LLM 생략, 캐시 파일에서 로드합니다.")
        schemas = _load_cache()
        if not schemas:
            print("캐시 파일이 없습니다. 일반 모드로 실행하세요.")
            return
    else:
        print("\n[1/3] 데이터 추출 중...")
        api_policies: list[RawApiPolicy] = []
        try:
            api_policies = await extract_policies_as_list()
            print(f"  ✓ 온통청년 API: {len(api_policies)}개")
        except Exception as e:
            print(f"  ✗ 온통청년 API 실패: {e}")

        crawled_policies: list[RawCrawledPolicy] = []
        try:
            crawled_policies = await crawl_bokjiro()
            print(f"  ✓ 복지로 크롤링: {len(crawled_policies)}개")
        except Exception as e:
            print(f"  ✗ 복지로 크롤링 실패: {e}")

        raw_items = _api_policies_to_raw(api_policies) + _crawled_to_raw(crawled_policies)
        before = len(raw_items)
        excluded_names = [item[2] for item in raw_items if not _is_relevant(item[2])]
        raw_items = [item for item in raw_items if _is_relevant(item[2])]

        if limit is not None:
            raw_items = raw_items[:limit]
            print(f"  → --limit {limit} 적용, 이후 단계는 이 {len(raw_items)}개만 처리")

        print(f"  → 총 추출: {before}개")
        print(f"  → 키워드 필터링: {before}개 → {len(raw_items)}개 ({len(excluded_names)}개 제외)")
        print("  → 제외된 정책 샘플 (상위 10개):")
        for name in excluded_names[:10]:
            print(f"     - {name}")

        if len(raw_items) == 0:
            print("추출된 데이터가 없습니다. 파이프라인 종료.")
            return

        print("\n[2/3] LLM 정형화 중...")
        schemas, credit_exhausted = await normalize_batch(
            raw_items,
            api_key=LLM_API_KEY,
            concurrency=2,
        )

        valid = [s for s in schemas if s is not None and not isinstance(s, Exception)]
        low_confidence = [s for s in valid if s.confidence < CONFIDENCE_THRESHOLD]

        print(f"  ✓ 정형화 성공: {len(valid)}개")
        print(f"  ⚠ confidence < {CONFIDENCE_THRESHOLD}: {len(low_confidence)}개 (삽입 제외)")
        print(f"  ✗ 정형화 실패: {len(raw_items) - len(valid)}개")

        if credit_exhausted:
            print("  ⚠ 크레딧 부족으로 중단됨 — 성공한 항목만 DB에 삽입합니다.")

        _save_cache(schemas)

    print("\n[3/3] policies_etl_staging 적재 중... (policies에는 아직 반영 안 됨)")
    result = await insert_batch(DB_DSN, schemas, source="etl_run")
    print(f"  ✓ 스테이징 적재: {result.success}개")
    print(f"  ⚠ 건너뜀:       {result.skipped}개 (confidence < 0.5)")
    print(f"  ✗ 실패:         {result.failed}개")
    print(f"  → 실제 반영은 python -m etl.promote list 로 검토 후 진행하세요.")

    if result.errors:
        print("\n[오류 목록]")
        for err in result.errors[:10]:
            print(f"  - {err}")
        if len(result.errors) > 10:
            print(f"  ... 외 {len(result.errors) - 10}개")

    print("\n" + "=" * 60)
    print("파이프라인 완료")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    use_cache = "--cache" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    asyncio.run(run_pipeline(use_cache=use_cache, limit=limit))