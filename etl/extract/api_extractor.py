import asyncio
import httpx
from dataclasses import dataclass


YOUTH_SEARCH_URL = "https://www.youthcenter.go.kr/pubot/search/portalPolicySearch"

SEARCH_PAYLOAD = {
    "PVSN_INST_GROUP_CD": "",
    "SPRT_TRGT_AGE": "",
    "EARN_MIN_AMT": "",
    "EARN_MAX_AMT": "",
    "QLFC_ACBG_NM": "",
    "MRG_STTS_CD": "",
    "query": "",
    "MJR_CND_NM": "",
    "EMPM_STTS_NM": "",
    "STDG_NM": "",
    "SPCL_FLD_NM": "",
    "USER_MCLSF_NO": "",
    "PLCY_KYWD_SN": "",
    "sortFields": "DATE/DESC",
    "listCount": 10,
    "searchFields": "all",
    "STDG_CTPV_NM": "서울특별시",
    "APLY_PRD_BGNG_YMD": "",
    "APLY_PRD_END_YMD": "",
    "APLY_PRD_SE_CD": "",
    "ODTM_CD": ""
}

HEADERS = {
    "Referer": "https://www.youthcenter.go.kr/",
    "Content-Type": "application/json",
}


@dataclass
class RawApiPolicy:
    policy_id: str
    name: str
    host_org: str
    target_region: str
    overview: str
    support_content: str
    age_min: str
    age_max: str
    apply_period: str
    source_url: str
    # 검색 API가 이미 구조화된 값으로 주는데도 예전엔 버려지던 필드들.
    # LLM이 텍스트에서 다시 추론하는 대신 그대로 신뢰할 수 있는 값들이라
    # 프롬프트에 명시적으로 실어 보낸다 (income_threshold/apply_start 등을
    # LLM이 잘못 재추정할 여지를 줄임).
    income_min_amt: str        # EARN_MIN_AMT — 소득 하한(중위소득 % 또는 원 단위, 정책마다 다름)
    income_max_amt: str        # EARN_MAX_AMT — 소득 상한
    apply_start_ymd: str       # APLY_PRD_BGNG_YMD — YYYYMMDD
    apply_end_ymd: str         # APLY_PRD_END_YMD — YYYYMMDD
    add_qualification: str     # ADD_APLY_QLFC_CND_CN — 추가 자격조건 (혼인여부, 자격증 등)
    apply_method: str          # PLCY_APLY_MTHD_CN — 신청 방법
    atch_file_mng_sn: str      # ATCH_FILE_MNG_SN — 첨부파일(공고문 PDF) 조회용 ID, 비어있으면 첨부 없음


async def _fetch_page(client: httpx.AsyncClient, page: int) -> dict:
    payload = {**SEARCH_PAYLOAD, "pageNum": page}
    resp = await client.post(YOUTH_SEARCH_URL, json=payload, headers=HEADERS, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


def _item_to_raw(item: dict) -> RawApiPolicy:
    policy_id = item.get("DOCID", "")
    return RawApiPolicy(
        policy_id=policy_id,
        name=item.get("PLCY_NM", "").replace('<span class="highlight">', "").replace("</span>", ""),
        host_org=item.get("SPRVSN_INST_CD_NM", ""),
        target_region=item.get("STDG_CTPV_NM", "서울특별시"),
        overview=item.get("PLCY_EXPLN_CN", "").replace('<span class="highlight">', "").replace("</span>", ""),
        support_content=item.get("PLCY_SPRT_CN", "").replace('<span class="highlight">', "").replace("</span>", ""),
        age_min=item.get("SPRT_TRGT_MIN_AGE", ""),
        age_max=item.get("SPRT_TRGT_MAX_AGE", ""),
        apply_period=item.get("APLY_PRD_SE_CD", ""),
        source_url=item.get("REF_URL_ADDR1", "") or f"https://www.youthcenter.go.kr/youthPolicy/ythPlcyTotalSearch",
        income_min_amt=item.get("EARN_MIN_AMT", ""),
        income_max_amt=item.get("EARN_MAX_AMT", ""),
        apply_start_ymd=item.get("APLY_PRD_BGNG_YMD", ""),
        apply_end_ymd=item.get("APLY_PRD_END_YMD", ""),
        add_qualification=item.get("ADD_APLY_QLFC_CND_CN", ""),
        apply_method=item.get("PLCY_APLY_MTHD_CN", ""),
        atch_file_mng_sn=item.get("ATCH_FILE_MNG_SN", ""),
    )


async def extract_policies_as_list() -> list[RawApiPolicy]:
    all_policies: list[RawApiPolicy] = []

    async with httpx.AsyncClient() as client:
        page = 1
        while True:
            data = await _fetch_page(client, page)
            items: list[dict] = data.get("searchResult", {}).get("youthpolicy", [])
            total: int = data.get("totalCount", 0)

            if not items:
                break

            all_policies.extend([_item_to_raw(item) for item in items])

            if len(all_policies) >= total:
                break

            page += 1
            await asyncio.sleep(0.3)

    return all_policies


if __name__ == "__main__":
    async def main():
        policies = await extract_policies_as_list()
        print(f"추출된 정책 수: {len(policies)}")
        if policies:
            print(f"첫 번째: {policies[0].name} / {policies[0].host_org}")
            print(f"마지막: {policies[-1].name}")

    asyncio.run(main())