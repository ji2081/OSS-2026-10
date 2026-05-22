import { useState } from "react";
import {
  DISTRICTS,
  EDUCATION_OPTIONS,
  HOUSING_OPTIONS,
} from "../data/subsidies";
import "./Sidebar.css";

function Sidebar({
  conditionSets,
  activeSetId,
  onSetChange,
  onAddSet,
  onRemoveSet,
  onRenameSet,
  condition,
  onUpdateCondition,
  onOptimize,
}) {
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h3>PROFILE INPUT</h3>
        <p>조건 설정</p>
      </div>

      <div className="condition-tabs">
        {conditionSets.map((s, index) => (
          <button
            key={s.id}
            className={`condition-tab ${s.id === activeSetId ? "active" : ""}`}
            onClick={() => onSetChange(s.id)}
          >
            {editingId === s.id ? (
              <input
                className="tab-edit-input"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onBlur={() => { onRenameSet(s.id, editName || `조건 ${index + 1}`); setEditingId(null); }}
                onKeyDown={(e) => { if (e.key === 'Enter') { onRenameSet(s.id, editName || `조건 ${index + 1}`); setEditingId(null); } }}
                onClick={(e) => e.stopPropagation()}
                autoFocus
              />
            ) : (
              <>
                {s.name || `조건 ${index + 1}`}
                <span className="tab-edit" onClick={(e) => { e.stopPropagation(); setEditingId(s.id); setEditName(s.name || `조건 ${index + 1}`); }}>✎</span>
              </>
            )}
            {conditionSets.length > 1 && (
              <span className="tab-remove" onClick={(e) => { e.stopPropagation(); onRemoveSet(s.id); }}>✕</span>
            )}
          </button>
        ))}
        {conditionSets.length < 4 && (
          <button className="condition-tab add-tab" onClick={onAddSet}>+</button>
        )}
      </div>

      <div className="sidebar-fields">
        {/* 나이 */}
        <div className="field-group">
          <div className="field-label-row">
            <label>나이</label>
            <span className="field-value">만 {condition.age}세</span>
          </div>
          <input
            type="range"
            min="19"
            max="34"
            value={condition.age}
            onChange={(e) => onUpdateCondition("age", Number(e.target.value))}
            className="slider"
          />
          <div className="slider-labels">
            <span>만 19세</span>
            <span>만 34세</span>
          </div>
        </div>

        {/* 연소득 */}
        <div className="field-group">
          <div className="field-label-row">
            <label>연소득</label>
            <span className="field-value">
              {condition.annualIncome === 0
                ? "소득 없음"
                : `${condition.annualIncome.toLocaleString()}만원`}
            </span>
          </div>
          <div className="income-input-wrap">
            <input
              type="number"
              min="0"
              max="10000"
              step="100"
              value={condition.annualIncome || ""}
              onChange={(e) =>
                onUpdateCondition("annualIncome", Number(e.target.value))
              }
              className="number-input"
              placeholder="0"
            />
            <span className="input-unit">만원</span>
          </div>
        </div>

        {/* 부모소득 */}
        <div className="field-group">
          <div className="field-label-row">
            <label>부모소득</label>
            <span className="field-value">
              {condition.parentIncome === 0
                ? "없음"
                : `${condition.parentIncome.toLocaleString()}만원`}
            </span>
          </div>
          <div className="income-input-wrap">
            <input
              type="number"
              min="0"
              max="30000"
              step="100"
              value={condition.parentIncome || ""}
              onChange={(e) =>
                onUpdateCondition("parentIncome", Number(e.target.value))
              }
              className="number-input"
              placeholder="0"
            />
            <span className="input-unit">만원</span>
          </div>
        </div>

        {/* 학력 · 취업 상태 */}
        <div className="field-group">
          <label>학력 · 취업 상태</label>
          <select
            value={condition.educationStatus}
            onChange={(e) =>
              onUpdateCondition("educationStatus", e.target.value)
            }
            className="select-input"
          >
            {EDUCATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* 거주 구 */}
        <div className="field-group">
          <label>거주 구</label>
          <select
            value={condition.district}
            onChange={(e) => onUpdateCondition("district", e.target.value)}
            className="select-input"
          >
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* 주거 형태 */}
        <div className="field-group">
          <label>주거 형태</label>
          <select
            value={condition.housingType}
            onChange={(e) => onUpdateCondition("housingType", e.target.value)}
            className="select-input"
          >
            {HOUSING_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* 토글 옵션들 */}
        <div className="toggle-section">
          <ToggleField
            label="취업 여부"
            checked={condition.isEmployed}
            onChange={(v) => onUpdateCondition("isEmployed", v)}
          />
          <ToggleField
            label="학자금 대출 여부"
            checked={condition.hasStudentLoan}
            onChange={(v) => onUpdateCondition("hasStudentLoan", v)}
          />
          <ToggleField
            label="중위소득 150% 이하"
            checked={condition.isBelow150Median}
            onChange={(v) => onUpdateCondition("isBelow150Median", v)}
          />
          <ToggleField
            label="차상위 계층"
            checked={condition.isNextTier}
            onChange={(v) => onUpdateCondition("isNextTier", v)}
          />
          <ToggleField
            label="기초수급자"
            checked={condition.isBasicLivelihood}
            onChange={(v) => onUpdateCondition("isBasicLivelihood", v)}
          />
        </div>
      </div>

      <div className="sidebar-footer">
        <button className="optimize-button" onClick={onOptimize}>
          <span className="optimize-icon">🔍</span>
          최적 조합 탐색
        </button>
        <p className="optimize-desc">현재 조건에 맞는 정책을 분석합니다</p>
      </div>
    </aside>
  );
}

function ToggleField({ label, checked, onChange }) {
  return (
    <div className="toggle-field">
      <span className="toggle-label">{label}</span>
      <button
        className={`toggle-switch ${checked ? "on" : ""}`}
        onClick={() => onChange(!checked)}
      >
        <span className="toggle-knob"></span>
      </button>
    </div>
  );
}

export default Sidebar;