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
  const [openFinanceBox, setOpenFinanceBox] = useState(false);
  const [openLoanBox, setOpenLoanBox] = useState(false);
  const [openDupGroups, setOpenDupGroups] = useState({});

  const toggleDupGroup = (groupId) => {
    setOpenDupGroups((prev) => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  const getCategoryColor = (catKey) => categories[catKey]?.color || "#999";
  const getCategoryLabel = (catKey) => categories[catKey]?.label || catKey;

  const grants = subsidies.filter(
    (s) => s.type === "confirmed" || s.type === "utilization",
  );
  const savings = subsidies.filter((s) => s.type === "savings");
  const loans = subsidies.filter((s) => s.type === "loan");

  const savingsDupGroups = duplicateGroups.filter((g) =>
    savings.find((s) => s.id === g.items[0]),
  );

  const grouped = {};
  grants.forEach((s) => {
    if (!grouped[s.category]) grouped[s.category] = [];
    grouped[s.category].push(s);
  });
  const catOrder = Object.keys(categories);

  const getConflictNames = (subsidy) => {
    if (!subsidy.exclusive_with || subsidy.exclusive_with.length === 0) return [];
    return subsidy.exclusive_with
      .map((id) => subsidies.find((p) => p.id === id)?.name)
      .filter(Boolean);
  };

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
          {subsidy.source_url && (
            <div className="detail-section">
              <span className="detail-label">신청</span>
              <a
                href={subsidy.source_url}
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
              <span className="status-badge" style={{ color: status.color, background: status.bg, border: status.dashed ? `1px dashed ${status.color}` : 'none' }}>{status.label}</span>
              {subsidy.exclusive_with?.length > 0 && (
                <span className="recommend-badge">추천</span>
              )}
              {subsidy.warning && (
                <span className="warning-badge">{subsidy.warning}</span>
              )}
            </div>
            <div className="subsidy-meta">
              <span>
                {subsidy.apply_start ? subsidy.apply_start : "일정 미정"}
                {subsidy.apply_end ? ` ~ ${subsidy.apply_end}` : ""}
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

      {savings.length > 0 && (
        <div className="finance-info-box">
          <div
            className="finance-info-header"
            onClick={() => setOpenFinanceBox(!openFinanceBox)}
          >
            <div className="finance-info-left">
              <span className="finance-info-icon">🏦</span>
              <div>
                <h4>청년 적금 · 금융상품</h4>
                <p>지원금은 아니지만 함께 활용하면 좋은 상품</p>
              </div>
            </div>
            <div className="finance-info-right">
              <span className="finance-info-count">{savings.length}개</span>
              <span className="finance-info-arrow">
                {openFinanceBox ? "▼" : "▶"}
              </span>
            </div>
          </div>
          {openFinanceBox && (
            <div className="finance-info-body">
              {savingsDupGroups.map((group) => {
                const isOpen = openDupGroups[group.id];
                const rec = subsidies.find((s) => s.id === group.recommendedId);
                const others = group.items.filter(
                  (id) => id !== group.recommendedId,
                );
                return (
                  <div key={group.id} className="finance-dup-group">
                    {group.items.map((itemId) => {
                      const item = subsidies.find((s) => s.id === itemId);
                      if (!item) return null;
                      return (
                        <div key={item.id} className="finance-item">
                          <div className="finance-item-left">
                            <span className="finance-item-name">
                              {item.name}
                            </span>
                            {item.id === group.recommendedId && (
                              <span className="recommend-badge">추천</span>
                            )}
                            {item.warning && (
                              <span className="warning-badge">
                                {item.warning}
                              </span>
                            )}
                          </div>
                          <span className="finance-item-desc">
                            {item.description}
                          </span>
                        </div>
                      );
                    })}
                    <div
                      className="dup-group-footer"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleDupGroup(group.id);
                      }}
                    >
                      <span className="dup-arrow">{isOpen ? "▼" : "▶"}</span>
                      <span className="dup-label">⚠️ 중복 제한</span>
                      <span className="dup-group-name">{group.name}</span>
                    </div>
                    {isOpen && (
                      <div className="dup-detail">
                        <div className="dup-recommend-box">
                          <div className="dup-rec-header">
                            <span className="dup-rec-badge">✅ 추천</span>
                            <span className="dup-rec-name">{rec?.name}</span>
                          </div>
                          <p className="dup-rec-reason">{group.reason}</p>
                        </div>
                        {others.map((id) => {
                          const o = subsidies.find((s) => s.id === id);
                          return (
                            <div key={id} className="dup-alt-box">
                              <span className="dup-alt-badge">대안</span>
                              <span className="dup-alt-name">{o?.name}</span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
              {savings
                .filter(
                  (s) => !savingsDupGroups.some((g) => g.items.includes(s.id)),
                )
                .map((item) => (
                  <div key={item.id} className="finance-item">
                    <div className="finance-item-left">
                      <span className="finance-item-name">{item.name}</span>
                      {item.warning && (
                        <span className="warning-badge">{item.warning}</span>
                      )}
                    </div>
                    <span className="finance-item-desc">
                      {item.description}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {loans.length > 0 && (
        <div className="finance-info-box loan-box">
          <div
            className="finance-info-header"
            onClick={() => setOpenLoanBox(!openLoanBox)}
          >
            <div className="finance-info-left">
              <span className="finance-info-icon">🏠</span>
              <div>
                <h4>청년 대출 · 주거지원</h4>
                <p>저금리 대출 등 주거 안정 지원 제도</p>
              </div>
            </div>
            <div className="finance-info-right">
              <span className="finance-info-count">{loans.length}개</span>
              <span className="finance-info-arrow">
                {openLoanBox ? "▼" : "▶"}
              </span>
            </div>
          </div>
          {openLoanBox && (
            <div className="finance-info-body">
              {loans.map((item) => (
                <div key={item.id} className="finance-item">
                  <div className="finance-item-left">
                    <span className="finance-item-name">{item.name}</span>
                    {item.warning && (
                      <span className="warning-badge">{item.warning}</span>
                    )}
                  </div>
                  <span className="finance-item-desc">{item.description}</span>
                  <span className="finance-item-provider">
                    {item.provider}
                    {item.source_url && (
                      <>
                        {" "}
                        ·{" "}
                        <a
                          href={item.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="detail-link"
                        >
                          신청 →
                        </a>
                      </>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SubsidyList;
