import asyncio
import httpx
from dataclasses import dataclass


BOKJIRO_SEARCH_URL = "https://www.bokjiro.go.kr/ssis-tbu/TWAT52005M/twataa/wlfareInfo/selectWlfareInfo.do"
BOKJIRO_DETAIL_URL = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId={}"

SEARCH_PAYLOAD = {
    "dmSearchParam": {
        "page": "1",
        "onlineYn": "",
        "searchTerm": "",
        "tabId": "1",
        "orderBy": "date",
        "bkjrLftmCycCd": "",
        "daesang": "",
        "period": "청년",
        "age": "",
        "region": "서울특별시",
        "jjim": "",
        "subject": "",
        "favoriteKeyword": "",
        "sidoCd": "1100000000",
        "sggCd": "",
        "endYn": ""
    },
    "dmScr": {
        "curScrId": "tbu/app/twat/twata/twataa/TWAT52005M",
        "befScrId": ""
    }
}

HEADERS = {
    "Referer": "https://www.bokjiro.go.kr/",
    "Content-Type": "application/json",
}


@dataclass
class RawCrawledPolicy:
    url: str
    name: str
    raw_text: str


async def _fetch_page(client: httpx.AsyncClient, page: int) -> dict:
    payload = {**SEARCH_PAYLOAD}
    payload["dmSearchParam"] = {**SEARCH_PAYLOAD["dmSearchParam"], "page": str(page)}
    resp = await client.post(BOKJIRO_SEARCH_URL, json=payload, headers=HEADERS, timeout=15.0)
    resp.raise_for_status()
    return resp.json()


async def _fetch_detail(client: httpx.AsyncClient, wlfare_id: str) -> str:
    url = BOKJIRO_DETAIL_URL.format(wlfare_id)
    resp = await client.get(url, headers=HEADERS, timeout=15.0)
    resp.raise_for_status()
    # 복지로 상세 페이지는 JS 렌더링이라 API로 직접 텍스트 구성
    return url


async def fetch_policy_list(client: httpx.AsyncClient) -> list[dict]:
    all_policies = []
    page = 1

    while True:
        data = await _fetch_page(client, page)
        items: list[dict] = data.get("dsServiceList0", [])
        if not items:
            break

        all_policies.extend(items)

        total = int(data.get("dmSearchParam", {}).get("totalCount", 0))
        if total and len(all_policies) >= total:
            break

        page += 1
        await asyncio.sleep(0.5)

    return all_policies


def _policy_to_raw_text(item: dict) -> str:
    return (
        f"정책명: {item.get('WLFARE_INFO_NM', '')}\n"
        f"주관기관: {item.get('BIZ_CHR_INST_NM', '')}\n"
        f"개요: {item.get('WLFARE_INFO_OUTL_CN', '')}\n"
        f"시행일: {item.get('ENFC_BGNG_YMD', '')}\n"
        f"종료일: {item.get('ENFC_END_YMD', '')}\n"
        f"문의처: {item.get('RPRS_CTADR', '')}\n"
        f"상세정보: {item.get('RETURN_STR', '')}\n"
    )


async def crawl_bokjiro() -> list[RawCrawledPolicy]:
    async with httpx.AsyncClient(verify=False) as client:
        items = await fetch_policy_list(client)
        print(f"복지로 수집: {len(items)}개")

    results = []
    for item in items:
        wlfare_id = item.get("WLFARE_INFO_ID", "")
        name = item.get("WLFARE_INFO_NM", "알 수 없음")
        url = BOKJIRO_DETAIL_URL.format(wlfare_id)
        raw_text = _policy_to_raw_text(item)
        results.append(RawCrawledPolicy(url=url, name=name, raw_text=raw_text))

    return results


if __name__ == "__main__":
    async def main():
        items = await crawl_bokjiro()
        print(f"크롤링 완료: {len(items)}개")
        for it in items[:3]:
            print(f"  - {it.name}")
            print(f"    {it.raw_text[:200]}")

    asyncio.run(main())