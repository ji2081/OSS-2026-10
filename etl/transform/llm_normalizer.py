import os
import json
import asyncio
import httpx
from openai import AsyncOpenAI
from pydantic import ValidationError

from etl.validate.schema import PolicySchema
from etl.extract.attachment_fetcher import fetch_main_pdf_bytes
from etl.extract.pdf_parser import extract_text, anchor_excerpt

# atch_file_mng_sn -> 추출된 PDF 전체 텍스트. 다운로드+파싱은 비용이 크므로
# 같은 첨부파일을 여러 번(재시도 등) 건드리게 되더라도 한 번만 하도록 캐싱한다.
_pdf_text_cache: dict[str, str] = {}


KNOWN_EXCLUSIVE_PAIRS: list[tuple[str, str]] = [
    ("국토교통부 청년월세 한시 특별지원", "서울시 청년월세지원"),
    ("청년 버팀목 전세자금대출", "중소기업취업청년 전월세보증금 대출"),
    ("희망두배청년통장", "청년 내일 저축계좌"),
    ("서울 청년수당", "국민취업지원제도"),
    ("청년 K-패스", "기후동행카드"),
]

SYSTEM_PROMPT = """
당신은 한국 청년 지원 정책 데이터를 구조화된 JSON으로 변환하는 전문 에이전트입니다.

반드시 아래 JSON 스키마를 따르세요. 누락된 필드는 null로 표시하고, 불확실한 값은 confidence를 낮게 설정하세요.

출력 형식 (JSON만, 마크다운 불포함):
{
  "title": "정책명 (string, 필수) - 띄어쓰기를 통일하고 공식 명칭 기준으로 정규화",
  "category": "housing | finance | employment | education | health | culture | welfare | startup | military | rights | scholarship",
  "benefit_type": "subsidy | loan | savings | voucher | interest_subsidy | goods | cashback | pass | training | other",
  "host_org": "주관기관명 (string)",
  "super_region": "전국 또는 광역시도명 (string)",
  "age_min": null 또는 정수,
  "age_max": null 또는 정수,
  "income_type": "median_pct(기준 중위소득 %) | annual_salary(연 소득 금액) | none(소득 무관)",
  "income_standard": null 또는 소득 기준 원문 그대로 요약한 문장 (예: "기준 중위소득 150% 이하"),
  "income_threshold": null 또는 소득 상한 숫자 (income_type이 median_pct면 150.0 같은 비율, annual_salary면 원 단위 금액),
  "income_threshold_min": null 또는 소득 하한 숫자 (하한이 있는 경우만, 예: 차상위 초과자만 대상이면 그 하한),
  "parent_income_threshold": null 또는 부모(가구원) 소득 기준 숫자 (본인 소득과 별도로 부모 소득을 보는 정책만),
  "target_unemployed_only": true 또는 false (미취업 청년 전용 여부),
  "situational_condition": null 또는 위 필드로 표현 안 되는 자격조건 자유서술 (예: "미혼자만 해당", "장애인 등록 필요", "다자녀 가구 우대"),
  "benefit_description": "수혜 내용 요약 (string)",
  "benefit_start_lag_days": 정수, 신청일로부터 실제 수혜 시작까지 지연일수 (불명확하면 0),
  "apply_start": null 또는 "YYYY-MM-DD",
  "apply_end": null 또는 "YYYY-MM-DD",
  "is_open_ended": true 또는 false ("상시모집"/"예산 소진 시" 등 마감일이 없는 경우 true),
  "exclusive_with": ["상호배타 정책명1", ...],
  "condition_tags": ["marital_unmarried", ...] (아래 태그 어휘집 중 해당하는 것만, 없으면 빈 배열),
  "is_supplementary": true 또는 false (아래 규칙 참고),
  "source_url": "출처 URL (string)",
  "confidence": 0.0~1.0 (float),
  "tiers": [
    {"max_income_ratio": null 또는 그 구간의 소득 상한(%), "monthly_benefit": 월 실수혜액(원, 정수), "duration_months": 수혜기간(월, 정수)}
  ]
}

tiers 작성 규칙 (가장 중요):
- 소득 구간마다 지원 금액이 다르면 tiers에 구간별로 항목을 나눠 넣으세요 (예: 중위소득 50% 이하는 월 30만원, 50~100%는 월 15만원 → 두 개의 tier).
- 구간 구분 없이 동일 금액을 지원하면 tiers에 max_income_ratio=null인 항목 하나만 넣으세요.
- monthly_benefit·duration_months는 반드시 "실질 수혜 가치" 기준으로 계산하세요. 이걸 잘못 계산하면 최적화 알고리즘이 완전히 엉뚱한 정책을 최선이라고 판단하게 됩니다.
  - 현금/보조금(subsidy): 월 지급액 그대로
  - 대출(loan): 원금이 아니라 우대금리로 인한 "이자 절감액"을 duration_months로 나눈 월 환산액 (예: 1억 × 1.2% × 2년 = 240만원 절감 → 24개월이면 월 10만원)
  - 저축 매칭(savings): 본인 납입분 제외, 정부 매칭분만 월 환산
  - 바우처/현물(voucher/goods): 현금 환산 가치를 월 환산
  - 실수혜액을 계산할 정보가 전혀 없으면 tiers를 빈 배열로 두고 benefit_description에 서술하세요 (그 경우 confidence를 낮추세요).
- 한 번만 지급되는 일시금이면 duration_months=1, monthly_benefit=그 금액.

condition_tags 태그 어휘집 (age/income_type/target_unemployed_only로 표현 안 되는 자격조건만, 반드시 아래 값만 사용):
- marital_unmarried: 미혼자만 해당
- disability_required: 장애인 등록 필요
- multicultural_family: 다문화가족만 해당
- single_parent: 한부모가족만 해당
- multi_child_household: 다자녀 가구만 해당
- veteran_or_family: 국가보훈대상자 본인/가족만 해당
- certification_holder: 특정 자격증 보유 필요
- dependent_household_member: 부양가족 있어야 함
위 목록에 없는 특이 조건은 situational_condition에 자유서술하고 condition_tags에는 넣지 마세요.

is_supplementary 판정 규칙:
- False(MWIS 후보): 직접 금전으로 지급되는 정책(subsidy/loan/savings/interest_subsidy/cashback 등)이면서 tiers를 계산할 수 있는 경우. 배타 관계가 없는 소액 정책(예: 자격증 응시료 지원)도 반드시 False로 두세요 — 배타가 없으면 "항상 선택해도 되는 정책"으로 자동 처리되므로 이런 소규모 정책일수록 놓치면 안 됩니다.
- True(보조/알짜배기 정보): 서비스·상담·바우처처럼 현금 환산이 부정확하거나 의미 없는 경우.

기타 규칙:
- 날짜가 "상시모집", "예산 소진 시", "미정" 등 파싱 불가한 경우 apply_start/apply_end는 null, is_open_ended는 true로 처리하세요.
- exclusive_with는 텍스트에 명시된 경우만 포함하세요. 상대 정책의 정확한 공식 명칭을 쓰세요(추후 이 이름으로 다른 정책과 매칭합니다).
- confidence: 명확한 출처 + 완전한 데이터 = 0.9~1.0, 추정 포함 = 0.6~0.8, 불명확 = 0.5 미만
- 서울 또는 전국 대상 정책만 처리하세요. 다른 지역 한정 정책은 confidence를 0.0으로 설정하세요.
- 재직자 전용 등 미취업 청년 대상이 아닌 정책은 confidence를 0.0으로 설정하세요.
- 나이 제한이 없는 경우 age_min, age_max는 null로 처리하세요. 절대 99999 같은 임의 값을 넣지 마세요.
- 소득 제한이 없는 경우 income_type은 "none", income_threshold 등은 null로 처리하세요.
""".strip()


def _get_known_exclusives_for(policy_name: str) -> list[str]:
    result = []
    for a, b in KNOWN_EXCLUSIVE_PAIRS:
        if policy_name in a or a in policy_name:
            result.append(b)
        elif policy_name in b or b in policy_name:
            result.append(a)
    return result


def _build_user_message(raw_text: str, source_url: str, known_exclusives: list[str], text_limit: int = 4000) -> str:
    exclusive_hint = ""
    if known_exclusives:
        exclusive_hint = f"\n\n[참고: 다음 정책들과 상호배타 관계일 수 있습니다: {', '.join(known_exclusives)}]"
    return f"출처: {source_url}\n\n정책 텍스트:\n{raw_text[:text_limit]}{exclusive_hint}"


def _extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


async def normalize_policy(
    client: AsyncOpenAI,
    raw_text: str,
    source_url: str,
    policy_name_hint: str = "",
    retries: int = 2,
) -> PolicySchema | None | str:
    known_exclusives = _get_known_exclusives_for(policy_name_hint)
    text_limits = [4000, 2000, 1000]

    for attempt in range(retries + 1):
        text_limit = text_limits[min(attempt, len(text_limits) - 1)]
        user_message = _build_user_message(raw_text, source_url, known_exclusives, text_limit)

        try:
            response = await client.chat.completions.create(
                model="claude-sonnet-5",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_message},
                ],
                # 스키마가 tiers 배열·situational_condition 등으로 확장되면서
                # 응답이 예전(1000)보다 길어져 JSON이 중간에 잘리는 사례가
                # 실측으로 확인됨 → 여유 있게 상향.
                max_tokens=2000,
            )
            raw_json = _extract_json(response.choices[0].message.content)
            data: dict = json.loads(raw_json)
            return PolicySchema(**data)

        except json.JSONDecodeError as e:
            if attempt == retries:
                print(f"[JSON FINAL FAIL] ({policy_name_hint}): {e}")
                return None
            print(f"[JSON RETRY {attempt + 1}] ({policy_name_hint}): {e}")
            await asyncio.sleep(1)

        except ValidationError as e:
            print(f"[SCHEMA ERROR] ({policy_name_hint})\n{e}")
            return None

        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "insufficient_quota" in err_str or "크레딧" in err_str:
                print(f"[CREDIT EXHAUSTED] ({policy_name_hint})")
                return "CREDIT_EXHAUSTED"
            if "429" in err_str:
                print(f"[RATE LIMIT] ({policy_name_hint}) 5초 대기 후 재시도...")
                await asyncio.sleep(5)
                continue
            print(f"[LLM ERROR] ({policy_name_hint}): {e}")
            return None

    return None


def _should_escalate_to_pdf(result: object) -> bool:
    """confidence==0.0은 '정보가 부족해서'가 아니라 프롬프트 규칙상 명시적으로
    배제 판정한 경우(지역 불일치·재직자 전용 등)라 PDF를 더 봐도 결론이
    바뀌지 않는다 — 이런 건 굳이 크레딧을 더 쓰지 않는다. 애매하게 낮은
    confidence거나, confidence는 있는데 tiers를 못 뽑은 경우만 승격한다."""
    if not isinstance(result, PolicySchema):
        return False
    if result.confidence <= 0.0:
        return False
    return result.confidence < 0.6 or len(result.tiers) == 0


async def _get_pdf_excerpt(http_client: httpx.AsyncClient, atch_file_mng_sn: str, policy_name: str) -> str | None:
    if atch_file_mng_sn not in _pdf_text_cache:
        try:
            pdf_bytes = await fetch_main_pdf_bytes(http_client, atch_file_mng_sn)
        except Exception as e:
            print(f"[PDF FETCH FAIL] atchFileMngSn={atch_file_mng_sn}: {e}")
            _pdf_text_cache[atch_file_mng_sn] = ""
            return None
        _pdf_text_cache[atch_file_mng_sn] = extract_text(pdf_bytes) if pdf_bytes else ""

    full_text = _pdf_text_cache[atch_file_mng_sn]
    if not full_text:
        return None
    return anchor_excerpt(full_text, policy_name)


async def normalize_policy_with_escalation(
    client: AsyncOpenAI,
    raw_text: str,
    source_url: str,
    policy_name_hint: str = "",
    http_client: httpx.AsyncClient | None = None,
    atch_file_mng_sn: str = "",
) -> PolicySchema | None | str:
    """1차: 검색 API 텍스트만으로 정형화. confidence가 낮거나 tiers를 못
    뽑았고 첨부 PDF가 있으면, PDF에서 정책명 주변만 잘라 붙여 한 번 더
    시도한다(=최대 2회 LLM 호출, 크레딧 통제를 위해 그 이상 재승격은 안 함)."""
    first = await normalize_policy(client, raw_text, source_url, policy_name_hint)

    if first == "CREDIT_EXHAUSTED":
        return first
    if not _should_escalate_to_pdf(first):
        return first
    if http_client is None or not atch_file_mng_sn:
        return first

    excerpt = await _get_pdf_excerpt(http_client, atch_file_mng_sn, policy_name_hint)
    if excerpt is None:
        return first

    print(f"[PDF 승격] ({policy_name_hint}) confidence={first.confidence:.2f}, tiers={len(first.tiers)}개 → PDF 재시도")
    augmented_text = f"{raw_text}\n\n[첨부 공고문 PDF 발췌]\n{excerpt}"
    second = await normalize_policy(client, augmented_text, source_url, policy_name_hint)

    if second == "CREDIT_EXHAUSTED":
        return second
    if not isinstance(second, PolicySchema):
        return first  # PDF까지 봤는데도 파싱 실패하면 1차 결과라도 살린다
    return second


async def normalize_batch(
    raw_items: list[tuple[str, str, str, str]],
    api_key: str,
    concurrency: int = 1,
    checkpoint_path: str = "etl_checkpoint.json",
) -> tuple[list[PolicySchema | None], bool]:

    checkpoint: dict[str, dict] = {}
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        print(f"  → 체크포인트 로드: {len(checkpoint)}개 이미 처리됨")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://factchat-cloud.mindlogic.ai/v1/gateway",
    )
    semaphore = asyncio.Semaphore(concurrency)
    results: list[PolicySchema | None] = [None] * len(raw_items)
    credit_exhausted = False

    async with httpx.AsyncClient(follow_redirects=True) as http_client:
        try:
            from etl.extract.attachment_fetcher import bootstrap_session
            await bootstrap_session(http_client)
        except Exception as e:
            print(f"[PDF 세션 부트스트랩 실패] PDF 승격 없이 진행: {e}")

        async def _normalize_with_sem(index: int, item: tuple[str, str, str, str]) -> None:
            nonlocal credit_exhausted
            if credit_exhausted:
                return

            raw_text, source_url, name, atch_file_mng_sn = item

            if name in checkpoint:
                try:
                    results[index] = PolicySchema(**checkpoint[name])
                except Exception:
                    pass
                return

            async with semaphore:
                if credit_exhausted:
                    return
                result = await normalize_policy_with_escalation(
                    client, raw_text, source_url, name,
                    http_client=http_client, atch_file_mng_sn=atch_file_mng_sn,
                )
                if result == "CREDIT_EXHAUSTED":
                    credit_exhausted = True
                    return
                results[index] = result

                if result is not None and not isinstance(result, Exception):
                    checkpoint[name] = result.model_dump(mode='json', serialize_as_any=True)
                    with open(checkpoint_path, 'w', encoding='utf-8') as f:
                        json.dump(checkpoint, f, ensure_ascii=False, default=str)

                await asyncio.sleep(2.0)

        tasks = [_normalize_with_sem(i, item) for i, item in enumerate(raw_items)]
        await asyncio.gather(*tasks, return_exceptions=True)

    return results, credit_exhausted