"""
PDF 바이트 → 텍스트, 그리고 큰 문서에서 필요한 부분만 잘라내는 앵커링.

실제로 첨부파일을 받아보면 두 종류가 섞여 있다:
  - 단일 정책 공고문 (몇백 KB, 몇 페이지) → 통으로 LLM에 넣어도 됨
  - 여러 제도를 묶은 종합 지침서 (100+ 페이지, 10만자+) → 통으로 넣으면
    낭비고, 정작 필요한 정책명 관련 대목은 문서 어딘가 뒤쪽에 있음

anchor_excerpt()는 정책명이 텍스트에 등장하는 위치를 찾아 그 앞뒤 구간만
잘라낸다. 이건 문자열 검색(str.find)이라 LLM 호출이 전혀 없다 — "어느
구간이 관련 있는지"를 LLM에게 묻지 않고 코드로 결정해서 크레딧을 아낀다.
"""
from __future__ import annotations

import io

import pdfplumber

# 단일 정책 공고문 정도로 보는 기준(문자 수). 이보다 짧으면 앵커링 없이
# 통째로 사용, 넘으면 정책명 주변만 잘라낸다.
SHORT_DOC_THRESHOLD = 6000

ANCHOR_BEFORE = 800
ANCHOR_AFTER = 3500


def extract_text(pdf_bytes: bytes) -> str:
    """PDF에서 텍스트만 뽑아낸다. 스캔본(이미지 PDF)이거나 손상된 파일이면
    빈 문자열을 반환한다(호출부에서 '추출 실패'로 처리하면 됨) — 예외를
    올려서 파이프라인 전체를 끊지 않는다."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            parts = [page.extract_text() or "" for page in pdf.pages]
        return "\n".join(parts)
    except Exception:
        return ""


_CLUSTER_WINDOW = 3000  # 이 범위 안에 다른 등장이 몇 번 더 있는지로 "진짜 상세 구간"을 고른다


def _find_all(text: str, keyword: str) -> list[int]:
    positions = []
    pos = 0
    while True:
        pos = text.find(keyword, pos)
        if pos == -1:
            return positions
        positions.append(pos)
        pos += 1


def _densest_occurrence(positions: list[int]) -> int:
    """여러 번 등장하는 문서(예: 여러 제도를 묶은 종합 지침서)에서는 맨 처음
    등장이 오히려 목차·개정이력 같은 스쳐 지나가는 언급일 때가 많다(실제로
    196페이지 지침서에서 확인된 패턴). 그래서 '주변에 같은 키워드가 가장
    많이 몰려있는 지점'을 실제 상세 설명 구간으로 보고 그 위치를 고른다."""
    best_pos, best_count = positions[0], -1
    for p in positions:
        count = sum(1 for q in positions if abs(q - p) <= _CLUSTER_WINDOW)
        if count > best_count:
            best_pos, best_count = p, count
    return best_pos


def anchor_excerpt(text: str, keyword: str, before: int = ANCHOR_BEFORE, after: int = ANCHOR_AFTER) -> str:
    """text에서 keyword가 가장 밀집되어 등장하는 구간을 찾아 그 앞뒤를 잘라
    반환한다. 문서가 SHORT_DOC_THRESHOLD보다 짧으면 그냥 전체를 반환한다.
    keyword를 못 찾으면(정책명 표기가 문서와 다른 경우 등) 문서 앞부분을
    반환하되, 못 찾았다는 표시를 남겨 confidence 판단에 참고할 수 있게 한다."""
    if len(text) <= SHORT_DOC_THRESHOLD:
        return text

    positions = _find_all(text, keyword)
    if not positions:
        # 정책명 전체가 아니라 앞 몇 어절만이라도 찾아본다 (LLM이 정규화한
        # 이름과 원문 표기가 완전히 같지 않을 수 있어서).
        short_keyword = keyword[: max(4, len(keyword) // 2)]
        positions = _find_all(text, short_keyword)
        keyword = short_keyword

    if not positions:
        return "[앵커 매칭 실패 — 문서 앞부분]\n" + text[: before + after]

    idx = _densest_occurrence(positions) if len(positions) > 1 else positions[0]
    start = max(0, idx - before)
    end = min(len(text), idx + len(keyword) + after)
    return text[start:end]
