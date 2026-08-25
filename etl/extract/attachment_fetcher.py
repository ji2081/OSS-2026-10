"""
온통청년 정책 공고문 첨부파일(PDF) 다운로드.

실제로 브라우저 네트워크 탭을 열어서 확인한 3단계 API:

1. 세션 부트스트랩 — 홈페이지를 한 번 GET하면 서버가 게스트 세션 쿠키
   (ygt, XSRF-TOKEN 등)를 내려준다. 이 쿠키 없이 아래 API를 바로 호출하면
   401 Unauthorized가 난다.
2. 첨부파일 목록 — GET /sur/com/atchFile/atchFileDet?atchFileMngSn={id}
   검색 API 응답의 ATCH_FILE_MNG_SN 필드를 그대로 넣으면 그 정책에 달린
   첨부파일 목록(파일명·확장자·크기)이 나온다.
3. 실제 다운로드 — GET /sur/com/atchFile/atchFileDetInfo/{atchFileMngSn}/{atchFileSn}
   인증 없이 그냥 GET하면 바이너리가 그대로 내려온다.

메인 공고문은 거의 항상 pdf고, 신청서·동의서 같은 부속 서류는 hwp인 경우가
많다(hwp 파싱은 훨씬 번거로워서 이번 범위에선 다루지 않는다). 그래서
pick_main_pdf()는 pdf 확장자만 후보로 보고, 그중 파일명이 "신청서"/"서약서"/
"동의서"/"제안서" 같은 부속 서류로 보이는 것은 제외해 메인 공고문을 고른다.
"""
from __future__ import annotations

import httpx

BASE_URL = "https://www.youthcenter.go.kr"
ATTACHMENT_LIST_PATH = "/sur/com/atchFile/atchFileDet"
ATTACHMENT_DOWNLOAD_PATH = "/sur/com/atchFile/atchFileDetInfo/{mng_sn}/{file_sn}"

# 첨부파일명에 이 단어가 있으면 "메인 공고문"이 아니라 부속 서류로 보고 제외한다.
_SUPPLEMENTARY_FILE_HINTS = ["신청서", "서약서", "동의서", "제안서", "서식", "양식"]


async def bootstrap_session(client: httpx.AsyncClient) -> None:
    """게스트 세션 쿠키 확보. client는 반드시 쿠키를 유지하는(기본값)
    httpx.AsyncClient여야 하고, 이후 같은 client로 나머지 요청을 보내야 한다."""
    resp = await client.get(BASE_URL + "/", timeout=15.0)
    resp.raise_for_status()


async def fetch_attachment_list(client: httpx.AsyncClient, atch_file_mng_sn: str) -> list[dict]:
    if not atch_file_mng_sn:
        return []
    resp = await client.get(
        BASE_URL + ATTACHMENT_LIST_PATH,
        params={"atchFileMngSn": atch_file_mng_sn, "isMaskingYn": "Y"},
        headers={"Referer": BASE_URL + "/"},
        timeout=15.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", {}).get("atchFileDetList", [])


def pick_main_pdf(attachments: list[dict]) -> dict | None:
    pdfs = [a for a in attachments if a.get("atchFileExtnNm", "").lower() == "pdf"]
    if not pdfs:
        return None
    main_candidates = [
        a for a in pdfs
        if not any(hint in a.get("exsFileNm", "") for hint in _SUPPLEMENTARY_FILE_HINTS)
    ]
    pool = main_candidates or pdfs
    # 여러 개 남으면 파일 크기가 제일 큰 것을 메인 공고문으로 추정 (부속
    # 참고자료보다 본문 공고문이 보통 더 길다).
    return max(pool, key=lambda a: a.get("atchFileSz", 0))


async def download_attachment(client: httpx.AsyncClient, atch_file_mng_sn: str, atch_file_sn: str) -> bytes:
    url = BASE_URL + ATTACHMENT_DOWNLOAD_PATH.format(mng_sn=atch_file_mng_sn, file_sn=atch_file_sn)
    resp = await client.get(url, headers={"Referer": BASE_URL + "/"}, timeout=60.0)
    resp.raise_for_status()
    return resp.content


async def fetch_main_pdf_bytes(client: httpx.AsyncClient, atch_file_mng_sn: str) -> bytes | None:
    """정책의 첨부파일 중 메인 공고문 PDF 하나를 다운로드해서 바이트로 반환.
    첨부가 없거나 PDF가 없으면 None."""
    attachments = await fetch_attachment_list(client, atch_file_mng_sn)
    main_pdf = pick_main_pdf(attachments)
    if main_pdf is None:
        return None
    return await download_attachment(client, atch_file_mng_sn, main_pdf["atchFileSn"])
