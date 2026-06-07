// pages/RoadmapPage.jsx — 수혜 로드맵 (간트차트)

import { useState, useRef, useEffect } from "react";
import "./RoadmapPage.css";

const ALL_CATEGORIES = {
  employment: { label: "취업·교육", color: "#FB8C00" },
  housing: { label: "주거", color: "#43A047" },
  finance: { label: "금융·자산", color: "#007AFF" },
  health: { label: "건강·복지", color: "#00BCD4" },
  culture: { label: "문화", color: "#FF375F" },
  military: { label: "군장병", color: "#5AC8FA" },
  education: { label: "교육·장학", color: "#8E24AA" },
};

const APP_WINDOWS = {
  "youth-allowance": { applyStart: "2025-07", applyEnd: "2025-07", duration: 6 },
  "rent-support-national": { applyStart: "2025-01", applyEnd: "2025-12", duration: 24 },
  "rent-support-seoul": { applyStart: "2025-06", applyEnd: "2025-06", duration: 12 },
  "tomorrow-savings": { applyStart: "2025-01", applyEnd: "2025-12", duration: 24 },
  "employment-support": { applyStart: "2025-01", applyEnd: "2025-06", duration: 6 },
  "loan-interest": { applyStart: "2025-01", applyEnd: "2025-09", duration: 12 },
  "exam-fee": { applyStart: "2025-01", applyEnd: "2025-12", duration: 1 },
  "transport-support": { applyStart: "2025-01", applyEnd: "2025-12", duration: 12 },
  kpass: { applyStart: "2025-01", applyEnd: "2025-12", duration: 12 },
  "hope-savings": { applyStart: "2025-06", applyEnd: "2025-06", duration: 36 },
  "nael-savings": { applyStart: "2025-05", applyEnd: "2025-05", duration: 36 },
  doyak: { applyStart: "2025-01", applyEnd: "2025-12", duration: 60, isAlwaysOpen: true },
  "jeonse-loan": { applyStart: "2025-01", applyEnd: "2025-12", duration: 24, isAlwaysOpen: true },
  "deposit-interest": { applyStart: "2025-01", applyEnd: "2025-12", duration: 84, isAlwaysOpen: true },
};

const ONE_TIME_IDS = new Set(["exam-fee"]);
const HANDOFFS = [
  { from: "employment-support", to: "tomorrow-savings" },
  { from: "rent-support-national", to: "rent-support-seoul" },
  { from: "kpass", to: "transport-support" },
];

function dateToAbs(dateStr) {
  if (!dateStr) return 0;
  const [y, m] = dateStr.split("-").map(Number);
  return y * 12 + (m - 1);
}
function absToYYYYMM(abs) {
  const y = Math.floor(abs / 12);
  const m = (abs % 12) + 1;
  return `${y}-${String(m).padStart(2, "0")}`;
}
function absToLabel(abs) { return absToYYYYMM(abs).replace("-", "."); }

function getMonthOptions(win) {
  if (!win) return [];
  const startAbs = dateToAbs(win?.applyStart);
  const endAbs = dateToAbs(win?.applyEnd);
  const options = [];
  for (let abs = startAbs; abs <= endAbs; abs++) options.push(absToYYYYMM(abs));
  return options;
}

function RoadmapPage({ subsidies, selectedSubsidies, hasOptimized, roadmapData }) {
  const selectedItems = roadmapData
    ? roadmapData.phases.flatMap((phase) =>
        phase.policies.map((p) => ({
          id: p.policy_id, name: p.title, category: p.category, type: "confirmed",
          amount: Math.round(p.total_benefit / 10000),
          apply_start: p.benefit_start?.substring(0, 7),
          apply_end: p.benefit_end?.substring(0, 7),
          duration_months: p.duration_months, phase_label: phase.label,
          provider: "", source_url: "", description: "",
          situational_condition: p.situational_condition || null,
        }))
      )
    : [];

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

  if (!hasOptimized || selectedItems.length === 0) {
    return (
      <div className="roadmap-page">
        <div className="roadmap-empty">
          <div className="roadmap-empty-icon">📋</div>
          <h3>{hasOptimized && !roadmapData ? "환승 로드맵 계산 중..." : "먼저 최적 조합을 탐색해주세요"}</h3>
          <p>대시보드에서 조건을 설정하고 "최적 조합 탐색"을 눌러주세요.</p>
        </div>
      </div>
    );
  }

  const getStartMonth = (item) => {
    if (selStart[item.id]) return selStart[item.id];
    return item.apply_start || null;
  };

  const getDuration = (item) => {
    if (item.duration_months) return item.duration_months;
    if (!item.apply_start || !item.apply_end) return 0;
    const s = dateToAbs(item.apply_start);
    const e = dateToAbs(item.apply_end);
    return Math.max(e - s + 1, 1);
  };

  const validStarts = selectedItems.map((s) => getStartMonth(s)).filter(Boolean);
  const baseAbs = validStarts.length > 0 ? Math.min(...validStarts.map(dateToAbs)) : dateToAbs("2026-06");
  const monthWidth = chartWidth / visibleMonths;

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

  const getBarProps = (item) => {
    const startMonth = getStartMonth(item);
    if (!startMonth) return { hidden: true };
    const startAbs2 = dateToAbs(startMonth);
    const duration = getDuration(item);
    const endAbs = startAbs2 + duration;
    const startOff = startAbs2 - baseAbs;
    const endOff = endAbs - baseAbs;
    const leftClamp = Math.max(0, startOff);
    const rightClamp = Math.min(endOff, visibleMonths);
    const left = leftClamp * monthWidth;
    const width = Math.max((rightClamp - leftClamp) * monthWidth, monthWidth * 0.4);
    return {
      left, width, startOff, endOff,
      extendsRight: endOff > visibleMonths,
      hidden: startOff >= visibleMonths || endOff <= 0,
      startLabel: absToLabel(startAbs2),
      endLabel: absToLabel(endAbs - 1),
    };
  };

  const totalAmount = selectedItems.filter((s) => s.amount).reduce((sum, s) => sum + s.amount, 0);
  const allEnds = selectedItems.filter((s) => getStartMonth(s)).map((s) => dateToAbs(getStartMonth(s)) + getDuration(s));
  const totalDuration = validStarts.length > 0 && allEnds.length > 0 ? Math.max(...allEnds) - Math.min(...validStarts.map(dateToAbs)) : 0;

  return (
    <div className="roadmap-page">
      <div className="roadmap-header">
        <div>
          <h2>수혜 로드맵</h2>
          <p className="roadmap-subtitle">{absToLabel(baseAbs)} ~ {absToLabel(baseAbs + visibleMonths - 1)} · 정책 지원 기간 시각화</p>
        </div>
        <div className="roadmap-stat-cards">
          <div className="rstat-card"><span className="rstat-label">총 수혜 기간</span><span className="rstat-value">{totalDuration}<span className="rstat-unit">개월</span></span></div>
          <div className="rstat-card"><span className="rstat-label">총 수혜액</span><span className="rstat-value accent">{totalAmount.toLocaleString()}<span className="rstat-unit">만원</span></span></div>
          <div className="rstat-card"><span className="rstat-label">정책 수</span><span className="rstat-value">{selectedItems.length}<span className="rstat-unit">개</span></span></div>
        </div>
      </div>

      <div className="roadmap-controls">
        <div className="roadmap-legend">
          {Object.entries(ALL_CATEGORIES)
            .filter(([key, cat], i, arr) => arr.findIndex(([, c]) => c.label === cat.label) === i)
            .map(([key, cat]) => (
              <div key={key} className="legend-item"><span className="legend-dot" style={{ background: cat.color }} /><span>{cat.label}</span></div>
            ))}
          <div className="legend-item"><span className="legend-handoff-icon">—›</span><span>인계 (핸드오프)</span></div>
          <div className="legend-item legend-hint"><span>ⓘ 항목 클릭 시 상세 보기</span></div>
        </div>
        <div className="period-control">
          <span className="period-label">표시 기간</span>
          <input type="range" min={1} max={24} value={visibleMonths} onChange={(e) => setVisibleMonths(Number(e.target.value))} className="period-slider" />
          <span className="period-value">{visibleMonths}개월</span>
        </div>
      </div>

      <div className="gantt-wrap">
        <div className="gantt-left">
          <div className="gantt-th-left">정책명</div>
          {selectedItems.map((item) => {
            const win = APP_WINDOWS[item.id];
            const options = win && !win.isAlwaysOpen ? getMonthOptions(win) : item.apply_start && item.apply_end ? getMonthOptions({ applyStart: item.apply_start, applyEnd: item.apply_end }) : [];
            const isAlwaysOpen = item.is_open_ended || (!item.apply_start && !item.apply_end);
            const curStart = getStartMonth(item);
            const color = ALL_CATEGORIES[item.category]?.color || "#999";
            return (
              <div key={item.id} className="gantt-row-left">
                <span className="gantt-dot" style={{ background: color }} />
                <div className="gantt-item-text">
                  <span className="gantt-item-name">{item.name}</span>
                  <span className="gantt-item-sub">{item.amount ? `${item.amount.toLocaleString()}만원` : "별도 안내"}</span>
                </div>
                {options.length > 1 ? (
                  <select className="month-select" value={curStart} onChange={(e) => setSelStart((prev) => ({ ...prev, [item.id]: e.target.value }))} onClick={(e) => e.stopPropagation()}>
                    {options.map((month) => <option key={month} value={month}>{month}</option>)}
                  </select>
                ) : isAlwaysOpen ? <span className="always-open-label">상시</span> : null}
              </div>
            );
          })}
        </div>

        <div className="gantt-right" ref={chartRef}>
          <div className="gantt-th-right">
            {quarters.map((q, i) => <div key={i} className="quarter-cell" style={{ width: q.months * monthWidth, minWidth: q.months * monthWidth }}>{q.label}</div>)}
          </div>
          {selectedItems.map((item) => {
            const bar = getBarProps(item);
            const color = ALL_CATEGORIES[item.category]?.color || "#999";
            const handoffIn = HANDOFFS.find((h) => h.to === item.id);
            const handoffOut = HANDOFFS.find((h) => h.from === item.id);
            return (
              <div key={item.id} className="gantt-row-right" onMouseLeave={() => setHoveredId(null)}>
                {quarters.map((q, i) => <div key={i} className="gantt-grid" style={{ left: q.offset * monthWidth, width: q.months * monthWidth }} />)}
                {handoffIn && !bar.hidden && bar.left > 24 && <div className="handoff-in" style={{ left: bar.left - 22 }}>—›</div>}
                {!bar.hidden && (
                  <div className={`gantt-bar${hoveredId === item.id ? " hovered" : ""}`} style={{ left: bar.left, width: bar.width, background: color }}
                    onMouseEnter={(e) => { setHoveredId(item.id); setTooltipPos({ x: e.clientX, y: e.clientY }); }}
                    onMouseMove={(e) => setTooltipPos({ x: e.clientX, y: e.clientY })}
                    onClick={() => setDetailItem(item)}>
                    <span className="bar-label">{bar.startLabel}</span>
                    {bar.extendsRight && <span className="bar-ext">›</span>}
                  </div>
                )}
                {handoffOut && !bar.hidden && !bar.extendsRight && <div className="handoff-out" style={{ left: bar.left + bar.width + 2 }}>—›</div>}
              </div>
            );
          })}
        </div>
      </div>

      {hoveredId && (() => {
        const item = selectedItems.find((s) => s.id === hoveredId);
        if (!item) return null;
        const bar = getBarProps(item);
        return <div className="gantt-tooltip" style={{ left: tooltipPos.x + 14, top: tooltipPos.y - 46 }}>{bar.startLabel} ~ {bar.endLabel}{item.amount ? ` · ${item.amount.toLocaleString()}만원` : ""}</div>;
      })()}

      {detailItem && (() => {
        const options = detailItem.apply_start && detailItem.apply_end ? getMonthOptions({ applyStart: detailItem.apply_start, applyEnd: detailItem.apply_end }) : [];
        const isAlwaysOpen = detailItem.is_open_ended || (!detailItem.apply_start && !detailItem.apply_end);
        const curStart = getStartMonth(detailItem);
        const duration = getDuration(detailItem);
        const endAbs = dateToAbs(curStart) + duration - 1;
        return (
          <div className="rm-overlay" onClick={() => setDetailItem(null)}>
            <div className="rm-modal" onClick={(e) => e.stopPropagation()}>
              <button className="rm-close" onClick={() => setDetailItem(null)}>✕</button>
              <div className="rm-dot" style={{ background: ALL_CATEGORIES[detailItem.category]?.color || "#999" }} />
              <h3 className="rm-title">{detailItem.name}</h3>
              <div className="rm-meta">
                <span>{detailItem.provider}</span>
                {detailItem.warning && <span className="rm-warn-badge">{detailItem.warning}</span>}
              </div>
              <div className="rm-amount">{detailItem.amount ? `${detailItem.amount.toLocaleString()}만원` : "별도 안내"}</div>
              <p className="rm-desc">{detailItem.description}</p>

              {detailItem.situational_condition && (
                <div className="rm-period-display">
                  <span className="rm-period-label">신청 조건</span>
                  <span className="rm-period-value">{detailItem.situational_condition}</span>
                </div>
              )}

              <div className="rm-period-display">
                <span className="rm-period-label">선택된 기간</span>
                <span className="rm-period-value">{curStart} ~ {absToYYYYMM(endAbs)} ({duration}개월)</span>
              </div>
              {options.length > 1 && (
                <div className="rm-windows">
                  <span className="rm-windows-title">신청 시작월 선택</span>
                  <p className="rm-windows-hint">신청 가능 기간: {detailItem.apply_start} ~ {detailItem.apply_end}</p>
                  <select className="rm-month-select" value={curStart} onChange={(e) => setSelStart((prev) => ({ ...prev, [detailItem.id]: e.target.value }))}>
                    {options.map((month) => <option key={month} value={month}>{month}</option>)}
                  </select>
                </div>
              )}
              {isAlwaysOpen && (
                <div className="rm-windows">
                  <span className="rm-windows-title">신청 기간</span>
                  <p className="rm-windows-hint">상시 신청 가능</p>
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
