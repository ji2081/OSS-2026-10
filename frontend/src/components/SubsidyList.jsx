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
  const catOrder = Object.keys(categories).sort((a, b) => {
    if (a === "scholarship") return -1;
    if (b === "scholarship") return 1;
    return 0;
  });
  const getConflictNames = (subsidy) => {
    if (!subsidy.exclusive_with || subsidy.exclusive_with.length === 0)
      return [];
    return subsidy.exclusive_with
      .map((id) => subsidies.find((p) => p.id === id)?.name)
      .filter(Boolean);
  };

  function DetailPanel({ subsidy }) {
    if (!subsidy) return null;
    const conflictNames = getConflictNames(subsidy);

    // 미래적금 ↔ 도약계좌 비교 텍스트
    const isFinanceCompare =
      subsidy.name?.includes("미래적금") || subsidy.name?.includes("도약계좌");

    return (
      <div className="detail-panel">
        <p className="detail-desc">{subsidy.description}</p>

        {/* situational_condition 표시 */}
        {subsidy.situational_condition && (
          <div className="detail-section">
            <span className="detail-label">신청 조건</span>
            <span className="detail-value">
              {subsidy.situational_condition}
            </span>
          </div>
        )}

        {/* 배타조건 상세 공지 */}
        {conflictNames.length > 0 && (
          <div className="detail-section detail-conflict-box">
            <span className="detail-label">⚠️ 중복 수급 불가 정책</span>
            <ul className="detail-conflict-list">
              {conflictNames.map((name, i) => (
                <li key={i}>{name}</li>
              ))}
            </ul>
            <p className="detail-conflict-note">
              위 정책과 동시에 수혜받을 수 없습니다. 하나만 선택해주세요.
            </p>
          </div>
        )}

        {/* 미래적금 ↔ 도약계좌 비교 */}
        {isFinanceCompare && (
          <div className="detail-section detail-compare-box">
            <span className="detail-label">📊 미래적금 vs 도약계좌 비교</span>
            <table className="detail-compare-table">
              <thead>
                <tr>
                  <th></th>
                  <th>청년미래적금</th>
                  <th>청년도약계좌</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>만기</td>
                  <td>3년</td>
                  <td>5년</td>
                </tr>
                <tr>
                  <td>월 납입 한도</td>
                  <td>50만원</td>
                  <td>70만원</td>
                </tr>
                <tr>
                  <td>기여금(일반)</td>
                  <td>납입의 6%</td>
                  <td>납입의 3~6%</td>
                </tr>
                <tr>
                  <td>기여금(우대)</td>
                  <td>납입의 12%</td>
                  <td>-</td>
                </tr>
                <tr>
                  <td>최대 수령액</td>
                  <td>약 2,000만원</td>
                  <td>약 5,000만원</td>
                </tr>
                <tr>
                  <td>비과세</td>
                  <td>O</td>
                  <td>O</td>
                </tr>
              </tbody>
            </table>
            <p className="detail-compare-tip">
              💡 단기 목돈이 필요하면 미래적금, 장기 자산형성이 목표면
              도약계좌가 유리합니다.
            </p>
          </div>
        )}

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
              {subsidy.exclusive_with?.length > 0 && (
                <span className="recommend-badge">추천</span>
              )}
              {subsidy.type === "utilization" && (
                <span className="utilization-badge">활용</span>
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
              {catKey === "scholarship" && (
                <span className="scholarship-notice">
                  ※ 본인 조건에 해당하는 장학금을 직접 선택해주세요
                </span>
              )}
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
