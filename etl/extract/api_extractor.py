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