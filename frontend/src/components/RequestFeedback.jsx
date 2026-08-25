import "./RequestFeedback.css";

function RequestFeedback({ status, title, message, onRetry, onDismiss }) {
  if (status === "loading") {
    return (
      <div className="request-loading-toast" role="status" aria-live="polite">
        <span className="request-spinner" aria-hidden="true" />
        <div>
          <strong>{title}</strong>
          <span>{message || "잠시만 기다려주세요."}</span>
        </div>
      </div>
    );
  }

  if (status !== "error") return null;

  return (
    <div className="request-error-overlay" role="presentation">
      <div
        className="request-error-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="request-error-title"
      >
        <div className="request-error-icon" aria-hidden="true">!</div>
        <h3 id="request-error-title">{title}</h3>
        <p>{message}</p>
        <div className="request-error-actions">
          {onDismiss && (
            <button className="request-close-button" onClick={onDismiss}>닫기</button>
          )}
          {onRetry && (
            <button className="request-retry-button" onClick={onRetry}>다시 시도</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default RequestFeedback;
