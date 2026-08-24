"""정책 자격조건 태그 어휘집.

age/income_level/region/is_employed(하드 필터)로 못 거르는 조건들 — 혼인여부,
장애 등록, 다문화가족, 자격증 보유 같은 것들 — 은 정책마다 케이스가 너무
다양해서 컬럼을 하나씩 만들 수 없다. 그렇다고 사용자에게 전부 미리 물어보면
회원가입 폼이 끝없이 길어지고, 본인도 관련 없는 질문에 답해야 한다.

그래서 이 어휘집은 고정된 태그 목록만 정의하고:
  - ETL(LLM)이 정책을 이 태그들로 분류해서 Policy.condition_tags에 저장
  - /optimize가 실제로 후보에 걸린 정책이 요구하는 태그만 추려서
    "확인 필요" 질문으로 사용자에게 보여줌 (services/policy_filter.py,
    routers/policy_router.py 참고)
  - 사용자가 답하면 UserProfile.confirmed_tags에 저장되고, 다음부턴 그
    태그에 대해 다시 안 물어봄

어휘집에 없는 특이 케이스는 Policy.situational_condition(자유 텍스트)에
남겨두고 화면에 참고용으로만 보여준다 — 필터링에는 안 쓰임. 반복적으로
나오는 패턴이 보이면 그때 이 목록에 태그를 추가하면 된다.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionTag:
    id: str
    question: str  # 사용자에게 보여줄 예/아니오 질문


CONDITION_TAGS: dict[str, ConditionTag] = {
    "marital_unmarried": ConditionTag(
        "marital_unmarried", "미혼이신가요?"),
    "disability_required": ConditionTag(
        "disability_required", "장애인으로 등록되어 있으신가요?"),
    "multicultural_family": ConditionTag(
        "multicultural_family", "다문화가족에 해당하시나요?"),
    "single_parent": ConditionTag(
        "single_parent", "한부모가족에 해당하시나요?"),
    "multi_child_household": ConditionTag(
        "multi_child_household", "다자녀 가구(자녀 2인 이상)에 해당하시나요?"),
    "veteran_or_family": ConditionTag(
        "veteran_or_family", "국가보훈대상자 본인 또는 가족이신가요?"),
    "certification_holder": ConditionTag(
        "certification_holder", "관련 자격증을 보유하고 계신가요?"),
    "dependent_household_member": ConditionTag(
        "dependent_household_member", "부양가족이 있으신가요?"),
}


def get_question(tag_id: str) -> str:
    tag = CONDITION_TAGS.get(tag_id)
    return tag.question if tag else f"'{tag_id}' 조건에 해당하시나요?"


def valid_tag_ids() -> set[str]:
    return set(CONDITION_TAGS.keys())
