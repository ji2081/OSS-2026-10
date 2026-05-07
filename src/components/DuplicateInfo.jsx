// components/DuplicateInfo.jsx — 중복 수혜 제한 안내 (아코디언)
//
// [핵심 개념] 아코디언 패턴
// 클릭하면 열리고/닫히는 UI. openGroups state로 어떤 그룹이 열려있는지 관리

import { useState } from 'react'
import './DuplicateInfo.css'

function DuplicateInfo({ groups, subsidies }) {
  // 어떤 그룹이 열려있는지 관리 (Set 대신 객체 사용)
  const [openGroups, setOpenGroups] = useState({})

  const toggleGroup = (groupId) => {
    setOpenGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }))
  }

  // subsidyId로 이름 찾기
  const getSubsidyName = (id) => {
    const s = subsidies.find(s => s.id === id)
    return s ? s.name : id
  }

  const getSubsidyAmount = (id) => {
    const s = subsidies.find(s => s.id === id)
    return s ? s.amount : 0
  }

  return (
    <div className="duplicate-info">
      <div className="duplicate-header">
        <span className="duplicate-icon">⚠️</span>
        <h3>중복 수혜 제한 안내</h3>
        <span className="duplicate-count">{groups.length}건</span>
      </div>

      <div className="duplicate-groups">
        {groups.map(group => {
          const isOpen = openGroups[group.id]
          const recommended = subsidies.find(s => s.id === group.recommendedId)
          const others = group.items.filter(id => id !== group.recommendedId)

          return (
            <div key={group.id} className="duplicate-group">
              {/* 그룹 요약 (클릭하면 열림) */}
              <button
                className="group-summary"
                onClick={() => toggleGroup(group.id)}
              >
                <div className="group-left">
                  <span className="group-arrow">{isOpen ? '▼' : '▶'}</span>
                  <div>
                    <span className="group-items">
                      {group.items.map(id => getSubsidyName(id)).join(' ↔ ')}
                    </span>
                    <span className="group-desc">{group.name}</span>
                  </div>
                </div>
                <span className="group-recommended-label">
                  추천: {recommended?.name}
                </span>
              </button>

              {/* 상세 내용 (아코디언) */}
              {isOpen && (
                <div className="group-detail">
                  {/* 추천 항목 */}
                  <div className="recommendation-box">
                    <div className="rec-header">
                      <span className="rec-badge">✅ 추천</span>
                      <span className="rec-name">{recommended?.name}</span>
                      <span className="rec-amount">
                        {recommended?.amount.toLocaleString()}만원
                      </span>
                    </div>
                    <p className="rec-reason">{group.reason}</p>
                  </div>

                  {/* 비교 대상 */}
                  {others.map(otherId => (
                    <div key={otherId} className="alternative-box">
                      <div className="alt-header">
                        <span className="alt-badge">대안</span>
                        <span className="alt-name">{getSubsidyName(otherId)}</span>
                        <span className="alt-amount">
                          {getSubsidyAmount(otherId).toLocaleString()}만원
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default DuplicateInfo
