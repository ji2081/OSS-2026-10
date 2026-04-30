import os
import asyncio
import json
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


def _api_policies_to_raw(items: list[RawApiPolicy]) -> list[tuple[str, str, str]]:
    return [
        (
            f"정책명: {p.name}\n주관기관: {p.host_org}\n대상지역: {p.target_region}\n"
            f"신청기간: {p.apply_period}\n개요: {p.overview}\n지원내용: {p.support_content}\n"
            f"대상나이: {p.age_min}~{p.age_max}세",
            p.source_url,
            p.name,
        )
        for p in items
    ]


def _crawled_to_raw(items: list[RawCrawledPolicy]) -> list[tuple[str, str, str]]:
    return [(it.raw_text, it.url, it.name) for it in items]


async def run_pipeline() -> None:
    print("=" * 60)
    print("청년 지원금 ETL 파이프라인 시작")
    print("=" * 60)

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
    total_extracted = len(raw_items)
    print(f"  → 총 추출: {total_extracted}개")

    if total_extracted == 0:
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
    print(f"  ✗ 정형화 실패: {total_extracted - len(valid)}개")

    if credit_exhausted:
        print("  ⚠ 크레딧 부족으로 중단됨 — 성공한 항목만 DB에 삽입합니다.")

    print("\n[3/3] DB 삽입 중...")
    result = await insert_batch(DB_DSN, schemas, source="etl_run")
    print(f"  ✓ 삽입 성공: {result.success}개")
    print(f"  ⚠ 건너뜀:   {result.skipped}개")
    print(f"  ✗ 실패:     {result.failed}개")

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
    asyncio.run(run_pipeline())