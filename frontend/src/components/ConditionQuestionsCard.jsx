import { useState } from "react";
import "./ConditionQuestionsCard.css";

// 지금 결과에 실제로 낀 정책이 요구하는 조건(미혼/장애 등)만 골라서
// 보여주는 카드. 전체 태그 목록을 미리 다 물어보는 게 아니라, 백엔드
// /policies/optimize가 pending_questions로 내려주는 것만 그려준다 —
// answering 하나가 오래 걸려도 이미 답한 질문은 answeringTag로 따로
// 표시해 버튼이 잠깐 잠기게만 하고 카드 전체를 막지 않는다.
function ConditionQuestionsCard({ questions, onAnswer }) {
  const [answeringTag, setAnsweringTag] = useState(null);

  if (!questions || questions.length === 0) return null;

  const handleClick = async (tag, value) => {
    setAnsweringTag(tag);
    try {
      await onAnswer(tag, value);
    } finally {
      setAnsweringTag(null);
    }
  };

  return (
    <div className="condition-questions-card">
      <div className="cq-header">
        <span className="cq-badge">확인 필요</span>
        <span className="cq-title">
          결과에 포함된 정책 중 아래 조건을 만족하는지 확인이 필요해요
        </span>
      </div>
      <ul className="cq-list">
        {questions.map((q) => (
          <li className="cq-item" key={q.tag}>
            <span className="cq-question">{q.question}</span>
            <div className="cq-actions">
              <button
                type="button"
                className="cq-btn cq-btn-yes"
                disabled={answeringTag === q.tag}
                onClick={() => handleClick(q.tag, true)}
              >
                예
              </button>
              <button
                type="button"
                className="cq-btn cq-btn-no"
                disabled={answeringTag === q.tag}
                onClick={() => handleClick(q.tag, false)}
              >
                아니오
              </button>
            </div>
          </li>
        ))}
      </ul>
      <p className="cq-note">
        답하지 않아도 결과에는 포함되지만, 실제 신청 전에 꼭 자격을 다시
        확인해주세요.
      </p>
    </div>
  );
}

export default ConditionQuestionsCard;
