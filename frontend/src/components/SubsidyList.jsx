import { useState } from "react";
import { getApplicationStatus } from "../data/subsidies";
import "./SubsidyList.css";

function SubsidyList({
  subsidies,
  selectedSubsidies,
  onToggle,
  categories,
  duplicateGroups,
  onResetToRecommended,
}) {
  const [expandedId, setExpandedId] = useState(null);

  const getCategoryColor = (catKey) => categories[catKey]?.color || "#999";
  const getCategoryLabel = (catKey) => categories[catKey]?.label || catKey;

  // confirmed + utilization 모두 체크리스트에 표시
  const grants = subsidies.filter(
    (s) => s.type === "confirmed" || s.type === "utilization",
  );

  const grouped = {};
  grants.forEach((s) => {
    if (!grouped[s.category]) grouped[s.category] = [];
    grouped[s.category].push(s);
  });
  const catOrder = Object.keys(categories);

  // 충돌 정책 이름 찾기
  const getConflictNames = (subsidy) => {
    if (!subsidy.duplicateWith || subsidy.duplicateWith.length === 0) return [];
    return subsidy.duplicateWith
      .map((id) => subsidies.find((p) => p.id === id)?.name)
      .filter(Boolean);
  };

  // 상세 패널
  function DetailPanel({ subsidy }) {
    if (!subsidy) return null;
    return (
      <div className="detail-panel">
        <p className="detail-desc">{subsidy.description}</p>
        {subsidy.documents && subsidy.documents.length > 0 && (
          <div className="detail-section">
            <span className="detail-label">필요 서류</span>
            <div className="detail-docs">
              {subsidy.documents.map((d, i) => (
                <span key={i} className="detail-doc">
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}
        <div className="detail-row">
          {subsidy.deadline && (
            <div className="detail-section">
              <span className="detail-label">마감일</span>
              <span className="detail-value">{subsidy.deadline}</span>
            </div>
          )}
          {subsidy.applyUrl && (
            <div className="detail-section">
              <span className="detail-label">신청</span>
              <a
                href={subsidy.applyUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="detail-link"
              >
                신청 페이지 →
              </a>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 정책 카드
  function PolicyCard({ subsidy, color }) {
    if (!subsidy.amount || subsidy.amount === 0) return null;
    const isSelected = selectedSubsidies[subsidy.id];
    const isExpanded = expandedId === subsidy.id;
    const status = getApplicationStatus(subsidy);
    const conflictNames = getConflictNames(subsidy);

    return (
      <div className="policy-card-wrapper">
        <div
          className={`subsidy-card ${isSelected ? "selected" : ""}`}
          onClick={() => setExpandedId(isExpanded ? null : subsidy.id)}
        >
          <input
            type="checkbox"
            className="subsidy-checkbox"
            checked={!!isSelected}
            onClick={(e) => e.stopPropagation()}
            onChange={(e) => {
              e.stopPropagation();
              onToggle(subsidy.id);
            }}
          />
          <div
            className="category-dot"
            style={{ backgroundColor: color }}
          ></div>
          <div className="subsidy-info">
            <div className="subsidy-name-row">
              <span className="subsidy-name">{subsidy.name}</span>
              <span
                className="status-badge"
                style={{
                  color: status.color,
                  background: status.bg,
                  border: status.dashed ? `1px dashed ${status.color}` : "none",
                }}
              >
                {status.label}
              </span>
              {subsidy.type === "utilization" && (
                <span className="utilization-badge">활용 수혜</span>
              )}
              {subsidy.warning && (
                <span className="warning-badge">{subsidy.warning}</span>
              )}
            </div>
            <div className="subsidy-meta">
              <span>
                {subsidy.startDate} ~ {subsidy.endDate}
              </span>
              <span>·</span>
              <span>{subsidy.provider}</span>
            </div>
          </div>
          <div className="subsidy-amount-area">
            <div className="subsidy-amount">
              {subsidy.amount ? subsidy.amount.toLocaleString() : "별도 안내"}
              <span className="amount-unit">만원</span>
            </div>
            <div className="expand-arrow">{isExpanded ? "▲" : "▼"}</div>
          </div>
        </div>
        {conflictNames.length > 0 && isSelected && (
          <div className="conflict-warning">
            ⚠️ <strong>{conflictNames.join(", ")}</strong>과(와) 중복 수혜 불가
          </div>
        )}
        {isExpanded && <DetailPanel subsidy={subsidy} />}
      </div>
    );
  }

  return (
    <div className="subsidy-list-container">
      <div className="list-header">
        <div className="list-header-left">
          <input
            type="checkbox"
            className="checkbox-all"
            checked={
              grants.length > 0 && grants.every((s) => selectedSubsidies[s.id])
            }
            onChange={() => onResetToRecommended()}
          />
          <h3>적용 가능 지원금</h3>
        </div>
        <span className="list-count">
          선택 {grants.filter((s) => selectedSubsidies[s.id]).length}개
        </span>
      </div>

      {catOrder.map((catKey) => {
        const items = (grouped[catKey] || []).filter(
          (s) => s.amount && s.amount > 0,
        );
        if (items.length === 0) return null;
        const color = getCategoryColor(catKey);
        const label = getCategoryLabel(catKey);

        return (
          <div key={catKey} className="category-section">
            <div
              className="category-section-header"
              style={{ borderLeftColor: color }}
            >
              <span
                className="category-section-dot"
                style={{ backgroundColor: color }}
              ></span>
              <span className="category-section-title">{label}</span>
              <span className="category-section-count">{items.length}개</span>
            </div>
            <div className="subsidy-cards">
              {items
                .sort((a, b) => b.amount - a.amount)
                .map((s) => (
                  <PolicyCard key={s.id} subsidy={s} color={color} />
                ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default SubsidyList;
