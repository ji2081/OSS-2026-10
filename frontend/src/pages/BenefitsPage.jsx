// pages/BenefitsPage.jsx — 알짜배기 정보
//
// ──────────────────────────────────────────────────────────────────────────────
// [DB 연동 가이드]
// benefitsToUse 배열을 API 응답으로 교체하면 본기능이 동작합니다.
// 각 혜택 객체의 스키마는 아래 타입 주석을 참고하세요.
// checkEligibility() 함수는 condition 객체와 benefit.eligibility를 비교합니다.
// ──────────────────────────────────────────────────────────────────────────────

import { useState } from "react";
import "./BenefitsPage.css";
import { getApplicationStatus } from '../data/subsidies'

// ── 카테고리 정의 ─────────────────────────────────────────────────────────────
export const BENEFIT_CATEGORIES = {
  all: { label: "전체", color: "#111" },
  culture: { label: "문화", color: "#FF375F" },
  employment: { label: "취업·교육", color: "#FF9F0A" },
  welfare: { label: "복지·서비스", color: "#5AC8FA" },
};

// ── 혜택 타입별 배경색 ────────────────────────────────────────────────────────
const TYPE_BG = {
  voucher: "#E8F6FE",
  discount: "#F0FFF4",
  goods: "#FFF8E6",
  service: "#F5F0FF",
  card: "#FFF0F5",
};

// ── 알짜배기 혜택 데이터 (더미) ───────────────────────────────────────────────
// [스키마]
// id          string   고유 ID
// name        string   혜택명
// category    string   BENEFIT_CATEGORIES의 key
// type        string   voucher | discount | goods | service | card
// typeLabel   string   타입 표시 레이블
// amount      number   지원액 (만원), 없으면 null
// amountLabel string   표시용 문자열
// provider    string   제공 기관
// description string   상세 설명
// howToApply  string   신청 방법
// applyUrl    string   신청 URL
// tags        string[] 태그 목록
// period      { start: 'YYYY-MM', end: 'YYYY-MM' } | null
// eligibility object   수혜 조건 (아래 checkEligibility() 참고)
// isOneTime   boolean  1회성 여부
// isRecurring boolean  반복 지원 여부
// ─────────────────────────────────────────────────────────────────────────────
export const BENEFITS_DATA = [
  // ── 문화 ──────────────────────────────────────────────────────────────────
  {
    id: "culture-voucher",
    name: "문화누리카드",
    category: "culture",
    type: "card",
    typeLabel: "이용권",
    amount: 13,
    amountLabel: "연 13만원",
    provider: "문화체육관광부",
    description:
      "문화예술·여행·체육 분야 이용권. 영화·공연·스포츠 관람, 국내여행, 온라인 콘텐츠 등 다양하게 활용 가능. 매년 갱신 발급.",
    howToApply:
      "읍면동 주민센터 방문 또는 문화누리카드 누리집(mnuri.kr) 온라인 신청",
    applyUrl: "https://www.mnuri.kr",
    tags: ["문화", "공연", "여행", "스포츠", "온라인콘텐츠"],
    period: { start: "2024-01", end: "2024-12" },
    eligibility: {
      anyOf: ["isBasicLivelihood", "isNextTier"],
    },
    isOneTime: false,
    isRecurring: true,
  },

  // ── 취업·교육 ─────────────────────────────────────────────────────────────
  {
    id: "skill-card",
    name: "국민내일배움카드",
    category: "employment",
    type: "card",
    typeLabel: "훈련비",
    amount: 500,
    amountLabel: "최대 500만원 (5년)",
    provider: "고용노동부",
    description:
      "직업훈련 비용 300~500만원 지원. 국민내일배움카드 발급 후 원하는 훈련 자유롭게 수강. 취업·이직·창업 준비에 활용 가능. 재직자·실업자 모두 신청 가능.",
    howToApply: "고용24(work.go.kr) 온라인 신청 또는 가까운 고용센터 방문",
    applyUrl: "https://www.work.go.kr",
    tags: ["직업훈련", "취업", "자격증", "재취업", "상시신청"],
    period: { start: "2024-01", end: "2027-12" },
    eligibility: {}, // 제한 없음 (누구나)
    isOneTime: false,
    isRecurring: false,
  },
  {
    id: "youth-job-voucher",
    name: "청년 취업 성공 패키지",
    category: "employment",
    type: "voucher",
    typeLabel: "바우처",
    amount: 195,
    amountLabel: "최대 195만원",
    provider: "고용노동부",
    description:
      "미취업 청년 대상 취업지원 서비스. 상담·훈련·취업 알선 3단계 지원. 참여수당 최대 195만원 지급. 취업 후 유지장려금 별도 지원.",
    howToApply: "고용24(work.go.kr) 또는 가까운 고용센터 방문 상담",
    applyUrl: "https://www.work.go.kr",
    tags: ["취업지원", "미취업", "상담", "훈련수당"],
    period: { start: "2024-01", end: "2024-12" },
    eligibility: {
      isEmployed: false, // 미취업자
    },
    isOneTime: false,
    isRecurring: false,
  },

  // ── 복지·서비스 ───────────────────────────────────────────────────────────
  {
    id: "mental-voucher",
    name: "청년 마음건강 바우처",
    category: "welfare",
    type: "voucher",
    typeLabel: "상담비",
    amount: 40,
    amountLabel: "최대 40만원",
    provider: "보건복지부",
    description:
      "심리상담 서비스 바우처. 전문 상담사 연계, 회당 본인부담 10%. 우울·불안·스트레스·자존감 등 정신건강 문제 지원. 1인당 연 최대 8회 지원.",
    howToApply: "복지로(bokjiro.go.kr) 또는 읍면동 주민센터 방문",
    applyUrl: "https://www.bokjiro.go.kr",
    tags: ["심리상담", "정신건강", "우울", "불안"],
    period: { start: "2024-04", end: "2024-09" },
    eligibility: { maxAge: 34 },
    isOneTime: true,
    isRecurring: false,
  },
  {
    id: "youth-mail",
    name: "청년 우편서비스 할인",
    category: "welfare",
    type: "discount",
    typeLabel: "할인",
    amount: 6,
    amountLabel: "연 최대 6만원 절감",
    provider: "우정사업본부",
    description:
      "등기우편·소포 발송 시 30% 할인 혜택. 청년 본인 확인 후 우체국 창구 또는 우체국 앱에서 즉시 적용. 건당 최대 3천원 할인.",
    howToApply:
      "우체국 창구 방문 (신분증 지참) 또는 우체국 앱 가입 후 할인 코드 등록",
    applyUrl: "https://www.epost.go.kr",
    tags: ["우편", "소포", "할인", "상시"],
    period: { start: "2024-01", end: "2025-12" },
    eligibility: { maxAge: 34 },
    isOneTime: false,
    isRecurring: true,
  },
  {
    id: "goods-support",
    name: "청년 생활용품 지원",
    category: "welfare",
    type: "goods",
    typeLabel: "물품지원",
    amount: 50,
    amountLabel: "약 50만원 상당",
    provider: "보건복지부",
    description:
      "독립 청년 생활필수품 꾸러미 지원. 주방용품·침구류·청소도구 등 입주 필수 물품으로 구성. 기초수급·차상위 독립 청년 우선 지원.",
    howToApply: "복지로(bokjiro.go.kr) 신청 또는 읍면동 주민센터 방문",
    applyUrl: "https://www.bokjiro.go.kr",
    tags: ["물품", "생필품", "독립청년", "입주"],
    period: { start: "2024-06", end: "2024-08" },
    eligibility: { anyOf: ["isBasicLivelihood", "isNextTier"] },
    isOneTime: true,
    isRecurring: false,
  },
  {
    id: "health-checkup",
    name: "청년 건강검진 지원",
    category: "welfare",
    type: "service",
    typeLabel: "서비스",
    amount: 20,
    amountLabel: "최대 20만원",
    provider: "국민건강보험공단",
    description:
      "청년 맞춤형 건강검진 항목 확대 지원. 기본 검진 외 정신건강·구강·시력 항목 추가. 직장 미가입 청년도 신청 가능.",
    howToApply: "국민건강보험공단(nhis.or.kr) 또는 가까운 검진기관 방문",
    applyUrl: "https://www.nhis.or.kr",
    tags: ["건강검진", "의료", "건강"],
    period: { start: "2024-01", end: "2024-12" },
    eligibility: { maxAge: 34 },
    isOneTime: false,
    isRecurring: true,
  },
];

// ── 수혜 자격 체크 ────────────────────────────────────────────────────────────
// [확장 방법]
// eligibility 객체에 새 조건 키를 추가하고 아래 함수에 분기를 추가하세요.
// anyOf: 배열 중 하나라도 만족하면 true
// allOf: 배열 전부 만족해야 true
// 개별 키: 직접 condition 속성과 비교
export function checkEligibility(benefit, condition) {
  const e = benefit.eligibility;
  if (!e || Object.keys(e).length === 0) return true;

  // anyOf 조건
  if (e.anyOf) {
    return e.anyOf.some((key) => condition[key]);
  }
  // allOf 조건
  if (e.allOf) {
    return e.allOf.every((key) => condition[key]);
  }
  // 개별 조건 체크
  if (e.maxAge !== undefined && condition.age > e.maxAge) return false;
  if (e.isEmployed !== undefined && condition.isEmployed !== e.isEmployed)
    return false;

  return true;
}

// ─────────────────────────────────────────────────────────────────────────────
function BenefitsPage({ condition, dbBenefits = [] }) {
  const [activeCategory, setActiveCategory] = useState("all");
  const [detailItem, setDetailItem] = useState(null);
  const benefitsToUse = dbBenefits.length > 0 ? dbBenefits : BENEFITS_DATA;

  const filtered = benefitsToUse.filter(
    (b) => activeCategory === "all" || b.category === activeCategory,
  );
  const eligible = filtered.filter((b) => checkEligibility(b, condition));
  const ineligible = filtered.filter((b) => !checkEligibility(b, condition));

  const countByCategory = (key) =>
    key === "all"
      ? benefitsToUse.length
      : benefitsToUse.filter((b) => b.category === key).length;

  return (
    <div className="benefits-page">
      {/* ── 헤더 ── */}
      <div className="benefits-header">
        <div>
          <h2>알짜배기 정보</h2>
          <p className="benefits-subtitle">
            바우처·할인·물품 등 현금 외 청년 혜택 모음
          </p>
        </div>
        <div className="benefits-stat">
          <span className="benefits-stat-num">{eligible.length}</span>
          <span className="benefits-stat-label">개 혜택 해당</span>
        </div>
      </div>

      {/* ── 카테고리 탭 ── */}
      <div className="benefits-tabs">
        {Object.entries(BENEFIT_CATEGORIES).map(([key, cat]) => (
          <button
            key={key}
            className={`benefits-tab${activeCategory === key ? " active" : ""}`}
            onClick={() => setActiveCategory(key)}
          >
            {key !== "all" && (
              <span className="tab-dot" style={{ background: cat.color }} />
            )}
            {cat.label}
            <span className="tab-count">{countByCategory(key)}</span>
          </button>
        ))}
      </div>

      {/* ── 해당 혜택 ── */}
      {eligible.length > 0 && (
        <>
          <div className="benefits-section-label">조건 해당 혜택</div>
          <div className="benefits-grid">
            {eligible.map((b) => (
              <BenefitCard
                key={b.id}
                benefit={b}
                onDetail={() => setDetailItem(b)}
              />
            ))}
          </div>
        </>
      )}

      {/* ── 기타 혜택 ── */}
      {ineligible.length > 0 && (
        <>
          <div className="benefits-section-label muted">
            기타 혜택 (조건 미해당)
          </div>
          <div className="benefits-grid">
            {ineligible.map((b) => (
              <BenefitCard
                key={b.id}
                benefit={b}
                onDetail={() => setDetailItem(b)}
                dimmed
              />
            ))}
          </div>
        </>
      )}

      {/* ── 상세 모달 ── */}
      {detailItem && (
        <div className="bp-overlay" onClick={() => setDetailItem(null)}>
          <div className="bp-modal" onClick={(e) => e.stopPropagation()}>
            <button className="bp-close" onClick={() => setDetailItem(null)}>
              ✕
            </button>

            <div className="bp-modal-top">
              <span
                className="bp-type-badge"
                style={{ background: TYPE_BG[detailItem.type] || "#F5F5F5" }}
              >
                {detailItem.typeLabel}
              </span>
              {detailItem.isOneTime && (
                <span className="bp-badge onetime">1회성</span>
              )}
              {detailItem.isRecurring && (
                <span className="bp-badge recurring">반복</span>
              )}
            </div>

            <h3 className="bp-modal-title">{detailItem.name}</h3>
            <p className="bp-modal-provider">{detailItem.provider}</p>
            <div className="bp-modal-amount">{detailItem.amountLabel}</div>
            <p className="bp-modal-desc">{detailItem.description}</p>

            <div className="bp-modal-tags">
              {detailItem.tags.map((t) => (
                <span key={t} className="bp-tag">
                  #{t}
                </span>
              ))}
            </div>

            <div className="bp-period">
  <span className="bp-period-label">지원 기간</span>
  <span>
    {detailItem.period && detailItem.period.start
      ? `${detailItem.period.start} ~ ${detailItem.period.end}`
      : '일정 미정'}
  </span>
</div>

            <div className="bp-how">
              <span className="bp-how-label">신청 방법</span>
              <p>{detailItem.howToApply}</p>
            </div>

            <a
              href={detailItem.source_url || detailItem.applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="bp-apply-btn"
            >
              신청하기 →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

// ── 카드 컴포넌트 ─────────────────────────────────────────────────────────────
function BenefitCard({ benefit, onDetail, dimmed }) {
  const catColor = BENEFIT_CATEGORIES[benefit.category]?.color || "#999";
 const status = getApplicationStatus({
  apply_start: benefit.period?.start || benefit.apply_start,
  apply_end: benefit.period?.end || benefit.apply_end,
  is_active: benefit.is_active !== false,
  is_open_ended: benefit.is_open_ended || benefit.isRecurring,
});
  return (
    <div
      className={`benefit-card${dimmed ? " dimmed" : ""}`}
      onClick={dimmed ? undefined : onDetail}
    >
      <div className="bc-top">
        <span
          className="bc-type"
          style={{ background: TYPE_BG[benefit.type] || "#F5F5F5" }}
        >
          {benefit.typeLabel}
        </span>
         <span className="status-badge" style={{ color: status.color, background: status.bg, border: status.dashed ? `1px dashed ${status.color}` : 'none' }}>{status.label}</span>
        {benefit.isOneTime && <span className="bc-badge onetime">1회성</span>}
        {benefit.isRecurring && (
          <span className="bc-badge recurring">반복</span>
        )}
      </div>

      <div className="bc-name-row">
        <span className="bc-dot" style={{ background: catColor }} />
        <span className="bc-name">{benefit.name}</span>
      </div>

      <p className="bc-desc">{benefit.description}</p>

      <div className="bc-bottom">
        {benefit.amountLabel !== "별도 안내" && (
          <span className="bc-amount">{benefit.amountLabel}</span>
        )}
        <span className="bc-provider">{benefit.provider}</span>
      </div>
    </div>
  );
}

export default BenefitsPage;
