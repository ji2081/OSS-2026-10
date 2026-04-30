import json
import asyncio
from openai import AsyncOpenAI
from pydantic import ValidationError

from etl.validate.schema import PolicySchema


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
  "category": "housing | finance | employment | education | health | culture | welfare | startup",
  "benefit_type": "subsidy | loan | savings | voucher | interest_subsidy | goods | cashback | pass | other",
  "host_org": "주관기관명 (string)",
  "super_region": "전국 또는 광역시도명 (string)",
  "sub_region": null 또는 "시군구명 (string)",
  "age_min": null 또는 정수,
  "age_max": null 또는 정수,
  "income_standard": null 또는 중위소득 % 숫자만 (예: 150.0),
  "income_limit": null 또는 원 단위 자산한도 정수,
  "total_benefit": null 또는 원 단위 정수,
  "benefit_duration_months": null 또는 수혜기간(월) 정수,
  "benefit_description": "수혜 내용 요약 (string)",
  "apply_start": null 또는 "YYYY-MM-DD",
  "apply_end": null 또는 "YYYY-MM-DD",
  "target_unemployed_only": true 또는 false (미취업 청년 전용 여부),
  "exclusive_with": ["상호배타 정책명1", ...],
  "source_url": "출처 URL (string)",
  "confidence": 0.0~1.0 (float)
}

규칙:
- total_benefit은 반드시 실질 수혜액 기준으로 계산하세요.
  - 현금/보조금: 수령 총액 (예: 월 20만원 × 12개월 = 2,400,000)
  - 대출: 이자 절감액 기준 (대출 원금이 아님. 예: 1억 × 1.2% × 2년 = 2,400,000)
  - 저축 매칭: 정부 매칭 총액 기준
  - 바우처/현물: 현금 환산 가치
- total_benefit 또는 benefit_description 중 하나는 반드시 있어야 합니다.
- 날짜가 "상시모집", "예산 소진 시", "미정" 등 파싱 불가한 경우 null로 처리하세요.
- exclusive_with는 텍스트에 명시된 경우만 포함하세요.
- confidence: 명확한 출처 + 완전한 데이터 = 0.9~1.0, 추정 포함 = 0.6~0.8, 불명확 = 0.5 미만
- 서울 또는 전국 대상 정책만 처리하세요. 다른 지역 한정 정책은 confidence를 0.0으로 설정하세요.
- 재직자 전용 등 미취업 청년 대상이 아닌 정책은 confidence를 0.0으로 설정하세요.
- benefit_type 선택 기준:
  - subsidy: 현금 지원금, 수당
  - loan: 대출
  - savings: 적금, 저축 매칭
  - voucher: 이용권, 바우처
  - interest_subsidy: 이자 지원
  - goods: 현물, 장비 지원
  - cashback: 교통 환급 등 캐시백
  - pass: 정기권 (교통 패스 등)
  - other: 위에 해당 없는 경우
  - target_unemployed_only: 재직자 지원 불가, 미취업 청년 전용인 경우 true. 불명확하면 false.
  - 나이 제한이 없는 경우 age_min, age_max는 null로 처리하세요. 절대 99999 같은 임의 값을 넣지 마세요.
  - 소득 제한이 없는 경우 income_standard는 null로 처리하세요.
  - benefit_duration_months는 실제 수혜 기간(개월)만 입력하세요. 불명확하면 null로 처리하세요.
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
) -> PolicySchema | None:
    known_exclusives = _get_known_exclusives_for(policy_name_hint)
    text_limits = [4000, 2000, 1000]

    for attempt in range(retries + 1):
        text_limit = text_limits[min(attempt, len(text_limits) - 1)]
        user_message = _build_user_message(raw_text, source_url, known_exclusives, text_limit)

        try:
            response = await client.chat.completions.create(
                model="claude-sonnet-4-5-20250929",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_message},
                ],
                max_tokens=1000,
            )
            raw_json = _extract_json(response.choices[0].message.content)
            data: dict = json.loads(raw_json)
            data["raw_data"] = raw_text[:2000]
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
            print(f"[LLM ERROR] ({policy_name_hint}): {e}")
            return None
        
        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "insufficient_quota" in err_str or "크레딧" in err_str:
                print(f"[CREDIT EXHAUSTED] ({policy_name_hint})")
                return "CREDIT_EXHAUSTED"
            print(f"[LLM ERROR] ({policy_name_hint}): {e}")
            return None

    return None


async def normalize_batch(
    raw_items: list[tuple[str, str, str]],
    api_key: str,
    concurrency: int = 2,
) -> tuple[list[PolicySchema | None], bool]:
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://factchat-cloud.mindlogic.ai/v1/gateway",
    )
    semaphore = asyncio.Semaphore(concurrency)
    results: list[PolicySchema | None] = [None] * len(raw_items)
    credit_exhausted = False

    async def _normalize_with_sem(index: int, item: tuple[str, str, str]) -> None:
        nonlocal credit_exhausted
        if credit_exhausted:
            return
        async with semaphore:
            if credit_exhausted:
                return
            result = await normalize_policy(client, item[0], item[1], item[2])
            if result == "CREDIT_EXHAUSTED":
                credit_exhausted = True
                return
            results[index] = result
            await asyncio.sleep(0.5)

    tasks = [_normalize_with_sem(i, item) for i, item in enumerate(raw_items)]
    await asyncio.gather(*tasks, return_exceptions=True)
    return results, credit_exhausted