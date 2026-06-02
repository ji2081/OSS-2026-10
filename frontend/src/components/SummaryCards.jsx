import "./SummaryCards.css";

function SummaryCards({
  totalAmount,
  confirmedAmount,
  utilizationAmount,
  selectedCount,
  totalCount,
  hasOptimized,
}) {
  return (
    <div className="summary-cards">
      {/* 선택 수혜액 */}
      <div className="summary-card">
        <div className="card-header">
          <span className="card-title">선택 수혜액</span>
          <span
            className="card-icon"
            style={{ background: "#E8F9EE", color: "#34C759" }}
          >
            ₩
          </span>
        </div>
        <div className="card-value">
          {hasOptimized ? (
            <>
              <span className="value-number">
                {totalAmount.toLocaleString()}
              </span>
              <span className="value-unit">만원</span>
            </>
          ) : (
            <span className="value-empty">—</span>
          )}
        </div>
        {hasOptimized && (
          <div className="card-breakdown">
            <span className="breakdown-item">
              확정 <strong>{confirmedAmount.toLocaleString()}만원</strong>
            </span>
            <span className="breakdown-divider">·</span>
            <span className="breakdown-item utilization">
              활용 시 추가{" "}
              <strong>+{utilizationAmount.toLocaleString()}만원</strong>
            </span>
          </div>
        )}
        <p className="card-desc">
          {hasOptimized ? "선택된 정책 합산" : "정책을 선택해주세요"}
        </p>
      </div>

      {/* 선택 정책 수 */}
      <div className="summary-card">
        <div className="card-header">
          <span className="card-title">선택 정책 수</span>
          <span
            className="card-icon"
            style={{ background: "#E8F6FE", color: "#5AC8FA" }}
          >
            📋
          </span>
        </div>
        <div className="card-value">
          {hasOptimized ? (
            <>
              <span className="value-number">{selectedCount}</span>
              <span className="value-unit">개</span>
            </>
          ) : (
            <span className="value-empty">0개</span>
          )}
        </div>
        <p className="card-desc">전체 {totalCount}개 중</p>
      </div>
    </div>
  );
}

export default SummaryCards;
