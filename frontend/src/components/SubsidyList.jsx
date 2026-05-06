import { useState } from 'react'
import './SubsidyList.css'

function SubsidyList({ subsidies, selectedSubsidies, onToggle, categories, duplicateGroups }) {
  const [openDupGroups, setOpenDupGroups] = useState({})
  const [openFinanceBox, setOpenFinanceBox] = useState(false)
  const [openLoanBox, setOpenLoanBox] = useState(false)

  const toggleDupGroup = (groupId) => {
    setOpenDupGroups(prev => ({ ...prev, [groupId]: !prev[groupId] }))
  }

  const getCategoryColor = (catKey) => {
    const cat = categories[catKey]
    return cat ? cat.color : '#999'
  }

  const getCategoryLabel = (catKey) => {
    const cat = categories[catKey]
    return cat ? cat.label : catKey
  }

  // 타입별 분리
  const grants = subsidies.filter(s => s.type === 'grant')
  const savings = subsidies.filter(s => s.type === 'savings')
  const loans = subsidies.filter(s => s.type === 'loan')

  // 지원금만 카테고리별 그룹핑
  const grouped = {}
  grants.forEach(s => {
    if (!grouped[s.category]) grouped[s.category] = []
    grouped[s.category].push(s)
  })

  const catOrder = Object.keys(categories)

  // 중복 그룹 중 grant 카테고리에 해당하는 것만
  const getDupGroupsForCategory = (catKey) => {
    return duplicateGroups.filter(g => {
      const firstItem = grants.find(s => s.id === g.items[0])
      return firstItem && firstItem.category === catKey
    })
  }

  // 적금 중복 그룹
  const savingsDupGroups = duplicateGroups.filter(g => {
    const firstItem = savings.find(s => s.id === g.items[0])
    return !!firstItem
  })

  return (
    <div className="subsidy-list-container">
      {/* ===== 지원금 메인 리스트 ===== */}
      <div className="list-header">
        <div className="list-header-left">
          <input
            type="checkbox"
            className="checkbox-all"
            checked={grants.every(s => selectedSubsidies[s.id])}
            onChange={() => {
              const allSelected = grants.every(s => selectedSubsidies[s.id])
              grants.forEach(s => {
                if (allSelected) onToggle(s.id)
                else if (!selectedSubsidies[s.id]) onToggle(s.id)
              })
            }}
          />
          <h3>적용 가능 지원금</h3>
        </div>
        <span className="list-count">선택 {grants.filter(s => selectedSubsidies[s.id]).length}개</span>
      </div>

      {catOrder.map(catKey => {
        const items = grouped[catKey]
        if (!items || items.length === 0) return null
        const color = getCategoryColor(catKey)
        const label = getCategoryLabel(catKey)
        const dupGroups = getDupGroupsForCategory(catKey)

        const dupItemIds = new Set()
        dupGroups.forEach(g => g.items.forEach(id => dupItemIds.add(id)))
        const normalItems = items.filter(s => !dupItemIds.has(s.id))

        return (
          <div key={catKey} className="category-section">
            <div className="category-section-header" style={{ borderLeftColor: color }}>
              <span className="category-section-dot" style={{ backgroundColor: color }}></span>
              <span className="category-section-title">{label}</span>
              <span className="category-section-count">{items.length}개</span>
            </div>

            <div className="subsidy-cards">
              {/* 중복 그룹 박스 */}
              {dupGroups.map(group => {
                const isOpen = openDupGroups[group.id]
                const recommended = subsidies.find(s => s.id === group.recommendedId)
                const others = group.items.filter(id => id !== group.recommendedId)

                return (
                  <div key={group.id} className="duplicate-group-box">
                    {group.items.map(itemId => {
                      const subsidy = subsidies.find(s => s.id === itemId)
                      if (!subsidy) return null
                      const isSelected = selectedSubsidies[subsidy.id]
                      const isRecommended = subsidy.id === group.recommendedId

                      return (
                        <div key={subsidy.id} className={`subsidy-card ${isSelected ? 'selected' : ''}`}>
                          <input
                            type="checkbox"
                            className="subsidy-checkbox"
                            checked={!!isSelected}
                            onChange={() => onToggle(subsidy.id)}
                          />
                          <div className="category-dot" style={{ backgroundColor: color }}></div>
                          <div className="subsidy-info">
                            <div className="subsidy-name-row">
                              <span className="subsidy-name">{subsidy.name}</span>
                              {isRecommended && <span className="recommend-badge">추천</span>}
                              {subsidy.warning && <span className="warning-badge">{subsidy.warning}</span>}
                            </div>
                            <div className="subsidy-meta">
                              <span>{subsidy.startDate} ~ {subsidy.endDate}</span>
                              <span>·</span>
                              <span>{subsidy.provider}</span>
                            </div>
                          </div>
                          <div className="subsidy-amount-area">
                            <div className="subsidy-amount">
                              {subsidy.amount.toLocaleString()}
                              <span className="amount-unit">만원</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                    <div className="dup-group-footer" onClick={() => toggleDupGroup(group.id)}>
                      <span className="dup-arrow">{isOpen ? '▼' : '▶'}</span>
                      <span className="dup-label">⚠️ 중복 제한</span>
                      <span className="dup-group-name">{group.name}</span>
                    </div>
                    {isOpen && (
                      <div className="dup-detail">
                        <div className="dup-recommend-box">
                          <div className="dup-rec-header">
                            <span className="dup-rec-badge">✅ 추천</span>
                            <span className="dup-rec-name">{recommended?.name}</span>
                            <span className="dup-rec-amount">{recommended?.amount.toLocaleString()}만원</span>
                          </div>
                          <p className="dup-rec-reason">{group.reason}</p>
                        </div>
                        {others.map(otherId => {
                          const other = subsidies.find(s => s.id === otherId)
                          return (
                            <div key={otherId} className="dup-alt-box">
                              <span className="dup-alt-badge">대안</span>
                              <span className="dup-alt-name">{other?.name}</span>
                              <span className="dup-alt-amount">{other?.amount.toLocaleString()}만원</span>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}

              {/* 일반 아이템 */}
              {normalItems.sort((a, b) => b.amount - a.amount).map(subsidy => {
                const isSelected = selectedSubsidies[subsidy.id]
                return (
                  <div key={subsidy.id} className={`subsidy-card ${isSelected ? 'selected' : ''}`}>
                    <input
                      type="checkbox"
                      className="subsidy-checkbox"
                      checked={!!isSelected}
                      onChange={() => onToggle(subsidy.id)}
                    />
                    <div className="category-dot" style={{ backgroundColor: color }}></div>
                    <div className="subsidy-info">
                      <div className="subsidy-name-row">
                        <span className="subsidy-name">{subsidy.name}</span>
                        {subsidy.warning && <span className="warning-badge">{subsidy.warning}</span>}
                      </div>
                      <div className="subsidy-meta">
                        <span>{subsidy.startDate} ~ {subsidy.endDate}</span>
                        <span>·</span>
                        <span>{subsidy.provider}</span>
                      </div>
                    </div>
                    <div className="subsidy-amount-area">
                      <div className="subsidy-amount">
                        {subsidy.amount.toLocaleString()}
                        <span className="amount-unit">만원</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}

      {/* ===== 적금 · 금융상품 안내 박스 ===== */}
      {savings.length > 0 && (
        <div className="finance-info-box">
          <div className="finance-info-header" onClick={() => setOpenFinanceBox(!openFinanceBox)}>
            <div className="finance-info-left">
              <span className="finance-info-icon">🏦</span>
              <div>
                <h4>청년 적금 · 금융상품</h4>
                <p>지원금은 아니지만 함께 활용하면 좋은 청년 금융상품</p>
              </div>
            </div>
            <div className="finance-info-right">
              <span className="finance-info-count">{savings.length}개</span>
              <span className="finance-info-arrow">{openFinanceBox ? '▼' : '▶'}</span>
            </div>
          </div>
          {openFinanceBox && (
            <div className="finance-info-body">
              {/* 적금 중복 그룹 */}
              {savingsDupGroups.map(group => {
                const isOpen = openDupGroups[group.id]
                const recommended = subsidies.find(s => s.id === group.recommendedId)
                const others = group.items.filter(id => id !== group.recommendedId)

                return (
                  <div key={group.id} className="finance-dup-group">
                    {group.items.map(itemId => {
                      const item = subsidies.find(s => s.id === itemId)
                      if (!item) return null
                      const isRec = item.id === group.recommendedId
                      return (
                        <div key={item.id} className="finance-item">
                          <div className="finance-item-left">
                            <span className="finance-item-name">{item.name}</span>
                            {isRec && <span className="recommend-badge">추천</span>}
                            {item.warning && <span className="warning-badge">{item.warning}</span>}
                          </div>
                          <span className="finance-item-desc">{item.description}</span>
                        </div>
                      )
                    })}
                    <div className="dup-group-footer" onClick={(e) => { e.stopPropagation(); toggleDupGroup(group.id) }}>
                      <span className="dup-arrow">{isOpen ? '▼' : '▶'}</span>
                      <span className="dup-label">⚠️ 중복 제한</span>
                      <span className="dup-group-name">{group.name}</span>
                    </div>
                    {isOpen && (
                      <div className="dup-detail">
                        <div className="dup-recommend-box">
                          <div className="dup-rec-header">
                            <span className="dup-rec-badge">✅ 추천</span>
                            <span className="dup-rec-name">{recommended?.name}</span>
                          </div>
                          <p className="dup-rec-reason">{group.reason}</p>
                        </div>
                        {others.map(otherId => {
                          const other = subsidies.find(s => s.id === otherId)
                          return (
                            <div key={otherId} className="dup-alt-box">
                              <span className="dup-alt-badge">대안</span>
                              <span className="dup-alt-name">{other?.name}</span>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}

              {/* 중복 그룹에 안 속하는 적금 */}
              {savings.filter(s => !savingsDupGroups.some(g => g.items.includes(s.id))).map(item => (
                <div key={item.id} className="finance-item">
                  <div className="finance-item-left">
                    <span className="finance-item-name">{item.name}</span>
                    {item.warning && <span className="warning-badge">{item.warning}</span>}
                  </div>
                  <span className="finance-item-desc">{item.description}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===== 대출 안내 박스 ===== */}
      {loans.length > 0 && (
        <div className="finance-info-box loan-box">
          <div className="finance-info-header" onClick={() => setOpenLoanBox(!openLoanBox)}>
            <div className="finance-info-left">
              <span className="finance-info-icon">🏠</span>
              <div>
                <h4>청년 대출 · 주거지원</h4>
                <p>저금리 대출 등 청년 주거 안정 지원 제도</p>
              </div>
            </div>
            <div className="finance-info-right">
              <span className="finance-info-count">{loans.length}개</span>
              <span className="finance-info-arrow">{openLoanBox ? '▼' : '▶'}</span>
            </div>
          </div>
          {openLoanBox && (
            <div className="finance-info-body">
              {loans.map(item => (
                <div key={item.id} className="finance-item">
                  <div className="finance-item-left">
                    <span className="finance-item-name">{item.name}</span>
                    {item.warning && <span className="warning-badge">{item.warning}</span>}
                  </div>
                  <span className="finance-item-desc">{item.description}</span>
                  <span className="finance-item-provider">{item.provider}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SubsidyList
