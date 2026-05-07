// pages/RoadmapPage.jsx — 수혜 로드맵 (간트차트)

import { useState, useRef, useEffect } from "react";
import "./RoadmapPage.css";

// ── 카테고리 (subsidies.js의 CATEGORIES + asset 포함) ─────────────────────────
const ALL_CATEGORIES = {
  living: { label: "생활지원", color: "#E53935" },
  realestate: { label: "주거", color: "#43A047" },
  employment: { label: "취업·교육", color: "#FB8C00" },
  transport: { label: "교통", color: "#8E24AA" },
  asset: { label: "자산형성", color: "#007AFF" },
};

// ── 신청 기간 데이터 ──────────────────────────────────────────────────────────
// applyStart ~ applyEnd : 신청 시작월을 선택할 수 있는 범위
// duration              : 정책이 지속되는 개월 수
// isAlwaysOpen          : true면 드롭다운 대신 "상시 신청" 표시
//
// [DB 연동] 이 객체를 API 응답으로 교체하면 됩니다.
const APP_WINDOWS = {
  "youth-allowance": {
    applyStart: "2025-07",
    applyEnd: "2025-07",
    duration: 6,
  },
  "rent-support-national": {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 24,
  },
  "rent-support-seoul": {
    applyStart: "2025-06",
    applyEnd: "2025-06",
    duration: 12,
  },
  "tomorrow-savings": {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 24,
  },
  "employment-support": {
    applyStart: "2025-01",
    applyEnd: "2025-06",
    duration: 6,
  },
  "loan-interest": { applyStart: "2025-01", applyEnd: "2025-09", duration: 12 },
  "exam-fee": { applyStart: "2025-01", applyEnd: "2025-12", duration: 1 },
  "transport-support": {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 12,
  },
  kpass: { applyStart: "2025-01", applyEnd: "2025-12", duration: 12 },
  "hope-savings": { applyStart: "2025-06", applyEnd: "2025-06", duration: 36 },
  "nael-savings": { applyStart: "2025-05", applyEnd: "2025-05", duration: 36 },
  doyak: {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 60,
    isAlwaysOpen: true,
  },
  "jeonse-loan": {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 24,
    isAlwaysOpen: true,
  },
  "deposit-interest": {
    applyStart: "2025-01",
    applyEnd: "2025-12",
    duration: 84,
    isAlwaysOpen: true,
  },
};

// ── 단발성 정책 (막대 1개월) ──────────────────────────────────────────────────
const ONE_TIME_IDS = new Set(["exam-fee"]);

// ── 인계(핸드오프) 관계 ────────────────────────────────────────────────────────
const HANDOFFS = [
  { from: "employment-support", to: "tomorrow-savings" },
  { from: "rent-support-national", to: "rent-support-seoul" },
  { from: "kpass", to: "transport-support" },
];

// ── 날짜 유틸 ────────────────────────────────────────────────────────────────
function dateToAbs(dateStr) {
  const [y, m] = dateStr.split("-").map(Number);
  return y * 12 + (m - 1);
}
function absToYYYYMM(abs) {
  const y = Math.floor(abs / 12);
  const m = (abs % 12) + 1;
  return `${y}-${String(m).padStart(2, "0")}`;
}
function absToLabel(abs) {
  return absToYYYYMM(abs).replace("-", ".");
}

// 신청 가능한 모든 월 목록 생성
function getMonthOptions(win) {
  if (!win) return [];
  const startAbs = dateToAbs(win.applyStart);
  const endAbs = dateToAbs(win.applyEnd);
  const options = [];
  for (let abs = startAbs; abs <= endAbs; abs++) {
    options.push(absToYYYYMM(abs));
  }
  return options;
}

// ─────────────────────────────────────────────────────────────────────────────
function RoadmapPage({ subsidies, selectedSubsidies, hasOptimized }) {
  const selectedItems = (subsidies || []).filter(
    (s) => selectedSubsidies?.[s.id],
  );

  const [visibleMonths, setVisibleMonths] = useState(24);
  const [selStart, setSelStart] = useState({});
  const [hoveredId, setHoveredId] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [detailItem, setDetailItem] = useState(null);

  const chartRef = useRef(null);
  const [chartWidth, setChartWidth] = useState(800);

  useEffect(() => {
    const el = chartRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => setChartWidth(el.offsetWidth || 800));
    obs.observe(el);
    setChartWidth(el.offsetWidth || 800);
    return () => obs.disconnect();
  }, []);

  // ── 빈 상태 ────────────────────────────────────────────────────────────────
  if (!hasOptimized || selectedItems.length === 0) {
    return (
      <div className="roadmap-page">
        <div className="roadmap-empty">
          <div className="roadmap-empty-icon">📋</div>
          <h3>먼저 최적 조합을 탐색해주세요</h3>
          <p>대시보드에서 조건을 설정하고 "최적 조합 탐색"을 눌러주세요.</p>
        </div>
      </div>
    );
  }

  // ── 활성 시작월 ────────────────────────────────────────────────────────────
  const getStartMonth = (item) => {
    const win = APP_WINDOWS[item.id];
    return selStart[item.id] ?? (win?.applyStart || item.startDate);
  };

  const getDuration = (item) => {
    if (ONE_TIME_IDS.has(item.id) || item.isOneTime) return 1;
    return (
      APP_WINDOWS[item.id]?.duration ??
      (() => {
        const s = dateToAbs(item.startDate);
        const e = dateToAbs(item.endDate);
        return Math.max(e - s + 1, 1);
      })()
    );
  };

  // ── 베이스 = 가장 빠른 시작월 ─────────────────────────────────────────────
  const baseAbs = Math.min(
    ...selectedItems.map((s) => dateToAbs(getStartMonth(s))),
  );
  const monthWidth = chartWidth / visibleMonths;

  // ── 분기 헤더 ─────────────────────────────────────────────────────────────
  const quarters = [];
  for (let offset = 0; offset < visibleMonths; ) {
    const abs = baseAbs + offset;
    const year = Math.floor(abs / 12);
    const mInYear = abs % 12;
    const q = Math.floor(mInYear / 3) + 1;
    const untilQEnd = 3 - (mInYear % 3);
    const qMonths = Math.min(untilQEnd, visibleMonths - offset);
    quarters.push({ label: `${year} Q${q}`, offset, months: qMonths });
    offset += qMonths;
  }

  // ── 막대 위치 계산 ────────────────────────────────────────────────────────
  const getBarProps = (item) => {
    const startAbs = dateToAbs(getStartMonth(item));
    const duration = getDuration(item);
    const endAbs = startAbs + duration;

    const startOff = startAbs - baseAbs;
    const endOff = endAbs - baseAbs;
    const leftClamp = Math.max(0, startOff);
    const rightClamp = Math.min(endOff, visibleMonths);
    const left = leftClamp * monthWidth;
    const width = Math.max(
      (rightClamp - leftClamp) * monthWidth,
      monthWidth * 0.4,
    );

    return {
      left,
      width,
      startOff,
      endOff,
      extendsRight: endOff > visibleMonths,
      hidden: startOff >= visibleMonths || endOff <= 0,
      startLabel: absToLabel(startAbs),
      endLabel: absToLabel(endAbs - 1),
    };
  };

  // ── 요약 통계 ─────────────────────────────────────────────────────────────
  const totalAmount = selectedItems
    .filter((s) => s.type === "grant" && s.amount)
    .reduce((sum, s) => sum + s.amount, 0);

  const allStarts = selectedItems.map((s) => dateToAbs(getStartMonth(s)));
  const allEnds = selectedItems.map(
    (s) => dateToAbs(getStartMonth(s)) + getDuration(s),
  );
  const totalDuration = Math.max(...allEnds) - Math.min(...allStarts);

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="roadmap-page">
      {/* ── 헤더 ── */}
      <div className="roadmap-header">
        <div>
          <h2>수혜 로드맵</h2>
          <p className="roadmap-subtitle">
            {absToLabel(baseAbs)} ~ {absToLabel(baseAbs + visibleMonths - 1)} ·
            정책 지원 기간 시각화
          </p>
        </div>
        <div className="roadmap-stat-cards">
          <div className="rstat-card">
            <span className="rstat-label">총 수혜 기간</span>
            <span className="rstat-value">
              {totalDuration}
              <span className="rstat-unit">개월</span>
            </span>
          </div>
          <div className="rstat-card">
            <span className="rstat-label">총 수혜액</span>
            <span className="rstat-value accent">
              {totalAmount.toLocaleString()}
              <span className="rstat-unit">만원</span>
            </span>
          </div>
          <div className="rstat-card">
            <span className="rstat-label">정책 수</span>
            <span className="rstat-value">
              {selectedItems.length}
              <span className="rstat-unit">개</span>
            </span>
          </div>
        </div>
      </div>

      {/* ── 범례 + 기간 슬라이더 ── */}
      <div className="roadmap-controls">
        <div className="roadmap-legend">
          {Object.entries(ALL_CATEGORIES).map(([key, cat]) => (
            <div key={key} className="legend-item">
              <span className="legend-dot" style={{ background: cat.color }} />
              <span>{cat.label}</span>
            </div>
          ))}
          <div className="legend-item">
            <span className="legend-handoff-icon">—›</span>
            <span>인계 (핸드오프)</span>
          </div>
          <div className="legend-item legend-hint">
            <span>ⓘ 항목 클릭 시 상세 보기</span>
          </div>
        </div>
        <div className="period-control">
          <span className="period-label">표시 기간</span>
          <input
            type="range"
            min={1}
            max={24}
            value={visibleMonths}
            onChange={(e) => setVisibleMonths(Number(e.target.value))}
            className="period-slider"
          />
          <span className="period-value">{visibleMonths}개월</span>
        </div>
      </div>

      {/* ── 간트차트 ── */}
      <div className="gantt-wrap">
        {/* 왼쪽: 정책명 열 */}
        <div className="gantt-left">
          <div className="gantt-th-left">정책명</div>
          {selectedItems.map((item) => {
            const win = APP_WINDOWS[item.id];
            const options =
              win && !win.isAlwaysOpen ? getMonthOptions(win) : [];
            const curStart = getStartMonth(item);
            const color = ALL_CATEGORIES[item.category]?.color || "#999";

            return (
              <div key={item.id} className="gantt-row-left">
                <span className="gantt-dot" style={{ background: color }} />
                <div className="gantt-item-text">
                  <span className="gantt-item-name">{item.name}</span>
                  <span className="gantt-item-sub">
                    {item.amount
                      ? `${item.amount.toLocaleString()}만원`
                      : "별도 안내"}
                  </span>
                </div>
                {options.length > 1 ? (
                  <select
                    className="month-select"
                    value={curStart}
                    onChange={(e) =>
                      setSelStart((prev) => ({
                        ...prev,
                        [item.id]: e.target.value,
                      }))
                    }
                    onClick={(e) => e.stopPropagation()}
                  >
                    {options.map((month) => (
                      <option key={month} value={month}>
                        {month}
                      </option>
                    ))}
                  </select>
                ) : win?.isAlwaysOpen ? (
                  <span className="always-open-label">상시</span>
                ) : null}
              </div>
            );
          })}
        </div>

        {/* 오른쪽: 타임라인 */}
        <div className="gantt-right" ref={chartRef}>
          <div className="gantt-th-right">
            {quarters.map((q, i) => (
              <div
                key={i}
                className="quarter-cell"
                style={{
                  width: q.months * monthWidth,
                  minWidth: q.months * monthWidth,
                }}
              >
                {q.label}
              </div>
            ))}
          </div>

          {selectedItems.map((item) => {
            const bar = getBarProps(item);
            const color = ALL_CATEGORIES[item.category]?.color || "#999";
            const handoffIn = HANDOFFS.find((h) => h.to === item.id);
            const handoffOut = HANDOFFS.find((h) => h.from === item.id);

            return (
              <div
                key={item.id}
                className="gantt-row-right"
                onMouseLeave={() => setHoveredId(null)}
              >
                {quarters.map((q, i) => (
                  <div
                    key={i}
                    className="gantt-grid"
                    style={{
                      left: q.offset * monthWidth,
                      width: q.months * monthWidth,
                    }}
                  />
                ))}

                {handoffIn && !bar.hidden && bar.left > 24 && (
                  <div className="handoff-in" style={{ left: bar.left - 22 }}>
                    —›
                  </div>
                )}

                {!bar.hidden && (
                  <div
                    className={`gantt-bar${hoveredId === item.id ? " hovered" : ""}`}
                    style={{
                      left: bar.left,
                      width: bar.width,
                      background: color,
                    }}
                    onMouseEnter={(e) => {
                      setHoveredId(item.id);
                      setTooltipPos({ x: e.clientX, y: e.clientY });
                    }}
                    onMouseMove={(e) =>
                      setTooltipPos({ x: e.clientX, y: e.clientY })
                    }
                    onClick={() => setDetailItem(item)}
                  >
                    <span className="bar-label">{bar.startLabel}</span>
                    {bar.extendsRight && <span className="bar-ext">›</span>}
                  </div>
                )}

                {handoffOut && !bar.hidden && !bar.extendsRight && (
                  <div
                    className="handoff-out"
                    style={{ left: bar.left + bar.width + 2 }}
                  >
                    —›
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── 툴팁 ── */}
      {hoveredId &&
        (() => {
          const item = selectedItems.find((s) => s.id === hoveredId);
          if (!item) return null;
          const bar = getBarProps(item);
          return (
            <div
              className="gantt-tooltip"
              style={{ left: tooltipPos.x + 14, top: tooltipPos.y - 46 }}
            >
              {bar.startLabel} ~ {bar.endLabel}
              {item.amount ? ` · ${item.amount.toLocaleString()}만원` : ""}
            </div>
          );
        })()}

      {/* ── 상세 모달 ── */}
      {detailItem &&
        (() => {
          const win = APP_WINDOWS[detailItem.id];
          const options = win && !win.isAlwaysOpen ? getMonthOptions(win) : [];
          const curStart = getStartMonth(detailItem);
          const duration = getDuration(detailItem);
          const endAbs = dateToAbs(curStart) + duration - 1;
          return (
            <div className="rm-overlay" onClick={() => setDetailItem(null)}>
              <div className="rm-modal" onClick={(e) => e.stopPropagation()}>
                <button
                  className="rm-close"
                  onClick={() => setDetailItem(null)}
                >
                  ✕
                </button>
                <div
                  className="rm-dot"
                  style={{
                    background:
                      ALL_CATEGORIES[detailItem.category]?.color || "#999",
                  }}
                />
                <h3 className="rm-title">{detailItem.name}</h3>
                <div className="rm-meta">
                  <span>{detailItem.provider}</span>
                  {detailItem.warning && (
                    <span className="rm-warn-badge">{detailItem.warning}</span>
                  )}
                </div>
                <div className="rm-amount">
                  {detailItem.amount
                    ? `${detailItem.amount.toLocaleString()}만원`
                    : "별도 안내"}
                </div>
                <p className="rm-desc">{detailItem.description}</p>

                <div className="rm-period-display">
                  <span className="rm-period-label">선택된 기간</span>
                  <span className="rm-period-value">
                    {curStart} ~ {absToYYYYMM(endAbs)} ({duration}개월)
                  </span>
                </div>

                {options.length > 1 && (
                  <div className="rm-windows">
                    <span className="rm-windows-title">신청 시작월 선택</span>
                    <p className="rm-windows-hint">
                      신청 가능 기간: {win.applyStart} ~ {win.applyEnd}
                    </p>
                    <select
                      className="rm-month-select"
                      value={curStart}
                      onChange={(e) =>
                        setSelStart((prev) => ({
                          ...prev,
                          [detailItem.id]: e.target.value,
                        }))
                      }
                    >
                      {options.map((month) => (
                        <option key={month} value={month}>
                          {month}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {win?.isAlwaysOpen && (
                  <div className="rm-windows">
                    <span className="rm-windows-title">신청 기간</span>
                    <p className="rm-windows-hint">
                      상시 신청 가능 ({win.applyStart} ~ {win.applyEnd})
                    </p>
                  </div>
                )}
              </div>
            </div>
          );
        })()}
    </div>
  );
}

export default RoadmapPage;
