import { useState } from 'react'
import Sidebar from '../components/Sidebar'
import SummaryCards from '../components/SummaryCards'
import SubsidyList from '../components/SubsidyList'
import logoImg from '../logo.png'
import './DashboardPage.css'
import { MOCK_SUBSIDIES, DUPLICATE_GROUPS, CATEGORIES, checkEligibility } from '../data/subsidies'

function DashboardPage({ userName, onLogout }) {
  const defaultCondition = {
    age: 24, annualIncome: 0, parentIncome: 0,
    housingType: 'monthly_rent', district: '관악구',
    hasStudentLoan: false, isBelow150Median: true,
    isEmployed: false, educationStatus: 'university',
    isNextTier: false, isBasicLivelihood: false,
  }
  const [conditionSets, setConditionSets] = useState([{ id: 1, name: '조건 1', ...defaultCondition }])
  const [activeSetId, setActiveSetId] = useState(1)
  const [nextId, setNextId] = useState(2)
  const activeCondition = conditionSets.find(s => s.id === activeSetId) || conditionSets[0]

 const addConditionSet = () => {
  if (conditionSets.length >= 4) return
  const newSet = { id: nextId, ...defaultCondition }
  setConditionSets([...conditionSets, newSet])
  setActiveSetId(nextId)
  setNextId(nextId + 1)
}
  const removeConditionSet = (id) => {
    if (conditionSets.length <= 1) return
    const filtered = conditionSets.filter(s => s.id !== id)
    setConditionSets(filtered)
    if (activeSetId === id) setActiveSetId(filtered[0].id)
  }
  const updateCondition = (field, value) => {
    setConditionSets(conditionSets.map(s => s.id === activeSetId ? { ...s, [field]: value } : s))
  }

  const [selectedSubsidies, setSelectedSubsidies] = useState({})
  const [filteredSubsidies, setFilteredSubsidies] = useState([])
  const [hasOptimized, setHasOptimized] = useState(false)

  const handleOptimize = () => {
    const eligible = MOCK_SUBSIDIES.filter(s => checkEligibility(s, activeCondition))
    setFilteredSubsidies(eligible)
    const newSelections = {}
    eligible.filter(s => s.type === 'grant').forEach(s => {
      if (s.duplicateGroup) {
        const group = DUPLICATE_GROUPS.find(g => g.id === s.duplicateGroup)
        newSelections[s.id] = group ? group.recommendedId === s.id : false
      } else {
        newSelections[s.id] = true
      }
    })
    setSelectedSubsidies(newSelections)
    setHasOptimized(true)
  }

  const toggleSubsidy = (subsidyId) => {
    const subsidy = MOCK_SUBSIDIES.find(s => s.id === subsidyId)
    if (subsidy && subsidy.duplicateGroup) {
      const group = DUPLICATE_GROUPS.find(g => g.id === subsidy.duplicateGroup)
      if (group) {
        setSelectedSubsidies(prev => {
          const next = { ...prev }
          group.items.forEach(id => { next[id] = false })
          next[subsidyId] = !prev[subsidyId]
          return next
        })
        return
      }
    }
    setSelectedSubsidies(prev => ({ ...prev, [subsidyId]: !prev[subsidyId] }))
  }

  const grants = filteredSubsidies.filter(s => s.type === 'grant')
  const selectedGrants = grants.filter(s => selectedSubsidies[s.id])
  const totalAmount = selectedGrants.reduce((sum, s) => sum + s.amount, 0)
  const selectedCount = selectedGrants.length
  const today = new Date()
  const dateStr = `${today.getFullYear()}.${String(today.getMonth()+1).padStart(2,'0')}.${String(today.getDate()).padStart(2,'0')} 기준`

  return (
    <div className="dashboard">
      <header className="dashboard-header">
       <div className="header-left">
          <img src={logoImg} alt="다바짜" style={{ width: 24, height: 24 }} />
          <h1>다바짜</h1>
          <span className="header-subtitle">청년지원금 최적조합탐색기</span>
        </div>
        <nav className="header-nav">
          <a href="#" className="nav-item active">대시보드</a>
          <a href="#" className="nav-item">수혜 로드맵</a>
        </nav>
        <div className="header-right">
          <span className="header-date">{dateStr}</span>
          <div className="header-user">
            <span>{userName}</span>
            <button onClick={onLogout} className="logout-btn">로그아웃</button>
          </div>
        </div>
      </header>
      <div className="dashboard-body">
        <Sidebar conditionSets={conditionSets} activeSetId={activeSetId} onSetChange={setActiveSetId} onAddSet={addConditionSet} onRemoveSet={removeConditionSet} condition={activeCondition} onUpdateCondition={updateCondition} onOptimize={handleOptimize} />
        <main className="dashboard-main">
          <div className="result-header">
            <div>
              <h2>지원금 분석 결과</h2>
              <p className="result-subtitle">
                만 {activeCondition.age}세 · {activeCondition.annualIncome === 0 ? '소득 없음' : `연소득 ${activeCondition.annualIncome.toLocaleString()}만원`} · 서울 {activeCondition.district} · {activeCondition.housingType === 'monthly_rent' ? '월세' : activeCondition.housingType === 'jeonse' ? '전세' : activeCondition.housingType === 'owned' ? '자가' : activeCondition.housingType === 'dormitory' ? '기숙사' : '무주택'}{activeCondition.parentIncome > 0 ? ` · 부모소득 ${activeCondition.parentIncome.toLocaleString()}만원` : ''}
              </p>
            </div>
          </div>
          <SummaryCards totalAmount={totalAmount} selectedCount={selectedCount} totalCount={grants.length} hasOptimized={hasOptimized} />
          {hasOptimized ? (
            <SubsidyList subsidies={filteredSubsidies} selectedSubsidies={selectedSubsidies} onToggle={toggleSubsidy} categories={CATEGORIES} duplicateGroups={DUPLICATE_GROUPS} />
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>조건을 설정하고 최적조합을 탐색해보세요</h3>
              <p>왼쪽 사이드바에서 조건을 입력한 후<br/>"최적 조합 탐색" 버튼을 눌러주세요.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
export default DashboardPage
