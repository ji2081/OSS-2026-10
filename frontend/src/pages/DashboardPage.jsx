import { useState } from "react";
import Sidebar from "../components/Sidebar";
import SummaryCards from "../components/SummaryCards";
import SubsidyList from "../components/SubsidyList";
import RoadmapPage from "./RoadmapPage";
import BenefitsPage from "./BenefitsPage";
import logoImg from "../logo.png";
import "./DashboardPage.css";
import {
  MOCK_SUBSIDIES,
  DUPLICATE_GROUPS,
  CATEGORIES,
  checkEligibility,
} from "../data/subsidies";

function DashboardPage({ userName, onLogout }) {
  const defaultCondition = {
    age: 24,
    annualIncome: 0,
    parentIncome: 0,
    housingType: "monthly_rent",
    district: "관악구",
    hasStudentLoan: false,
    isBelow150Median: true,
    isEmployed: false,
    educationStatus: "university",
    isNextTier: false,
    isBasicLivelihood: false,
  };

  const [currentPage, setCurrentPage] = useState("dashboard");

  const [conditionSets, setConditionSets] = useState([
    { id: 1, name: "", ...defaultCondition },
  ]);
  const [activeSetId, setActiveSetId] = useState(1);
  const [nextId, setNextId] = useState(2);
  const activeCondition =
    conditionSets.find((s) => s.id === activeSetId) || conditionSets[0];

  const addConditionSet = () => {
    if (conditionSets.length >= 4) return;
    const newSet = { id: nextId, name: "", ...defaultCondition };
    setConditionSets([...conditionSets, newSet]);
    setActiveSetId(nextId);
    setNextId(nextId + 1);
  };
  const removeConditionSet = (id) => {
    if (conditionSets.length <= 1) return;
    const filtered = conditionSets.filter((s) => s.id !== id);
    setConditionSets(filtered);
    if (activeSetId === id) setActiveSetId(filtered[0].id);
  };
  const updateCondition = (field, value) => {
    setConditionSets(
      conditionSets.map((s) =>
        s.id === activeSetId ? { ...s, [field]: value } : s,
      ),
    );
  };
  const renameConditionSet = (id, newName) => {
    setConditionSets(
      conditionSets.map((s) => (s.id === id ? { ...s, name: newName } : s)),
    );
  };

  const [selectedSubsidies, setSelectedSubsidies] = useState({});
  const [filteredSubsidies, setFilteredSubsidies] = useState([]);
  const [hasOptimized, setHasOptimized] = useState(false);
  const [extraBenefits, setExtraBenefits] = useState([]);

  const handleOptimize = async () => {
    try {
      const backendUrl = `http://${window.location.hostname}:8000`;
      const res = await fetch(`${backendUrl}/policies/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({
          profile: {
            age: activeCondition.age,
            income_level:
              activeCondition.annualIncome === 0
                ? 0
                : activeCondition.isBelow150Median
                  ? 1
                  : 2,
            is_employed: activeCondition.isEmployed,
            region: "서울",
            sub_region: activeCondition.district,
          },
          min_confidence: 0.5,
        }),
      });
      const data = await res.json();
      console.log("백엔드 응답:", data);

      const categoryMap = {
        housing: "realestate",
        finance: "asset",
        employment: "employment",
        education: "employment",
        health: "living",
        culture: "culture",
        welfare: "living",
        startup: "employment",
      };
      const typeMap = {
        subsidy: "grant",
        interest_subsidy: "grant",
        loan: "loan",
        savings: "savings",
        voucher: "voucher",
        goods: "service",
        cashback: "service",
        pass: "service",
        other: "service",
      };
      const benefitCatMap = {
        employment: "employment",
        realestate: "welfare",
        living: "welfare",
        transport: "welfare",
        asset: "welfare",
        culture: "culture",
      };

      const now = new Date();
      const year = now.getFullYear();
      const nextMonth = now.getMonth() + 2;
      const nextMonthStr = `${nextMonth > 12 ? year + 1 : year}-${String(nextMonth > 12 ? 1 : nextMonth).padStart(2, "0")}`;

      const mapPolicy = (p) => ({
        id: p.id,
        name: p.title,
        category: categoryMap[p.category] || "living",
        type: typeMap[p.benefit_type] || "grant",
        amount:
          p.tiers && p.tiers.length > 0
            ? Math.round(
                (p.tiers[0].monthly_benefit * p.tiers[0].duration_months) /
                  10000,
              )
            : 0,
        startDate: p.apply_start ? p.apply_start.slice(0, 7) : nextMonthStr,
        endDate: p.apply_end ? p.apply_end.slice(0, 7) : `${year}-12`,
        provider: p.host_org || "",
        isDuplicate: (p.exclusive_with || []).length > 0,
        duplicateGroup: null,
        duplicateWith: p.exclusive_with || [],
        warning: p.target_unemployed_only ? "미취업자" : null,
        description: p.benefit_description || "",
        documents: [],
        applyUrl: p.source_url,
        deadline: p.apply_end,
      });

      const toBenefit = (p) => ({
        id: p.id,
        name: p.name,
        category: benefitCatMap[p.category] || "welfare",
        type: p.type,
        typeLabel:
          p.type === "loan" ? "대출" : p.type === "savings" ? "적금" : "서비스",
        amount: null,
        amountLabel: "별도 안내",
        provider: p.provider,
        description: p.description,
        applyUrl: p.applyUrl,
        tags: [],
        period: p.startDate ? { start: p.startDate, end: p.endDate } : null,
        eligibility: {},
        isOneTime: false,
        isRecurring: false,
        howToApply: "해당 기관 홈페이지 또는 방문 신청",
      });

      const converted = data.selected_policies.map(mapPolicy);
      const supplementaryConverted = (data.supplementary_policies || []).map(
        mapPolicy,
      );

      // amount 있는 것 → 대시보드, 없는 것 → 알짜배기
      const mainPolicies = converted.filter(
        (p) => p.type === "grant" || p.type === "loan" || p.type === "savings",
      );
      const nullAsBenefits = converted
        .filter((p) => p.type === "voucher" || p.type === "service")
        .map(toBenefit);

      const suppMain = supplementaryConverted.filter(
        (p) => p.type === "grant" || p.type === "loan" || p.type === "savings",
      );
      const suppBenefits = supplementaryConverted
        .filter((p) => p.type === "voucher" || p.type === "service")
        .map(toBenefit);

      setFilteredSubsidies([...mainPolicies, ...suppMain]);
      setExtraBenefits([...nullAsBenefits, ...suppBenefits]);

      const newSelections = {};
      mainPolicies.forEach((s) => {
        newSelections[s.id] = true;
      });

      const allPolicies = [...mainPolicies, ...suppMain];
      allPolicies
        .filter((s) => s.type === "grant" && s.amount && s.amount > 0)
        .forEach((s) => {
          const hasConflictSelected = (s.duplicateWith || []).some((id) => {
            const conflictPolicy = allPolicies.find((p) => p.id === id);
            return newSelections[id] && conflictPolicy?.type === "grant";
          });
          if (!hasConflictSelected) {
            newSelections[s.id] = true;
          }
        });

      setSelectedSubsidies(newSelections);
      setHasOptimized(true);

      console.log("백엔드 추천 총액:", data.total_benefit);
    } catch (err) {
      console.error("API 에러:", err);
      const eligible = MOCK_SUBSIDIES.filter((s) =>
        checkEligibility(s, activeCondition),
      );
      setFilteredSubsidies(eligible);
      const newSelections = {};
      eligible
        .filter((s) => s.type === "grant")
        .forEach((s) => {
          if (s.duplicateGroup) {
            const group = DUPLICATE_GROUPS.find(
              (g) => g.id === s.duplicateGroup,
            );
            newSelections[s.id] = group ? group.recommendedId === s.id : false;
          } else {
            newSelections[s.id] = true;
          }
        });
      setSelectedSubsidies(newSelections);
      setHasOptimized(true);
    }
  };

  const toggleSubsidy = (subsidyId) => {
    const subsidy = filteredSubsidies.find((s) => s.id === subsidyId);

    if (subsidy && subsidy.duplicateWith && subsidy.duplicateWith.length > 0) {
      setSelectedSubsidies((prev) => {
        const next = { ...prev };
        subsidy.duplicateWith.forEach((id) => {
          next[id] = false;
        });
        next[subsidyId] = !prev[subsidyId];
        return next;
      });
      return;
    }

    setSelectedSubsidies((prev) => ({
      ...prev,
      [subsidyId]: !prev[subsidyId],
    }));
  };

  const dynamicDupGroups = [];
  const processed = new Set();
  filteredSubsidies
    .filter((s) => s.type === "grant")
    .forEach((s) => {
      if (s.duplicateWith?.length > 0 && !processed.has(s.id)) {
        const conflictingGrants = s.duplicateWith.filter((id) => {
          const p = filteredSubsidies.find((p) => p.id === id);
          return p && p.type === "grant";
        });
        if (conflictingGrants.length > 0) {
          const group = [s.id, ...conflictingGrants];
          group.forEach((id) => processed.add(id));
          const conflictNames = conflictingGrants
            .map((id) => filteredSubsidies.find((p) => p.id === id)?.name)
            .filter(Boolean)
            .join(", ");
          dynamicDupGroups.push({
            id: s.id,
            name: "중복 제한",
            items: group,
            recommendedId: s.id,
            reason: `${conflictNames}과(와) 동시에 수혜 불가합니다.`,
          });
        }
      }
    });
  const grants = filteredSubsidies.filter((s) => s.type === "grant");
  const selectedGrants = grants.filter((s) => selectedSubsidies[s.id]);
  const totalAmount = selectedGrants.reduce((sum, s) => sum + s.amount, 0);
  const selectedCount = selectedGrants.length;
  const today = new Date();
  const dateStr = `${today.getFullYear()}.${String(today.getMonth() + 1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")} 기준`;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <img src={logoImg} alt="다바짜" style={{ width: 24, height: 24 }} />
          <h1>다바짜</h1>
          <span className="header-subtitle">청년지원금 최적조합탐색기</span>
        </div>
        <nav className="header-nav">
          <a
            href="#"
            className={`nav-item${currentPage === "dashboard" ? " active" : ""}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentPage("dashboard");
            }}
          >
            대시보드
          </a>
          <a
            href="#"
            className={`nav-item${currentPage === "roadmap" ? " active" : ""}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentPage("roadmap");
            }}
          >
            수혜 로드맵
          </a>
          <a
            href="#"
            className={`nav-item${currentPage === "benefits" ? " active" : ""}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentPage("benefits");
            }}
          >
            알짜배기 정보
          </a>
        </nav>
        <div className="header-right">
          <span className="header-date">{dateStr}</span>
          <div className="header-user">
            <span>{userName}</span>
            <button onClick={onLogout} className="logout-btn">
              로그아웃
            </button>
          </div>
        </div>
      </header>

      {currentPage === "dashboard" && (
        <div className="dashboard-body">
          <Sidebar
            conditionSets={conditionSets}
            activeSetId={activeSetId}
            onSetChange={setActiveSetId}
            onAddSet={addConditionSet}
            onRemoveSet={removeConditionSet}
            onRenameSet={renameConditionSet}
            condition={activeCondition}
            onUpdateCondition={updateCondition}
            onOptimize={handleOptimize}
          />
          <main className="dashboard-main">
            <div className="result-header">
              <div>
                <h2>지원금 분석 결과</h2>
                <p className="result-subtitle">
                  만 {activeCondition.age}세 ·{" "}
                  {activeCondition.annualIncome === 0
                    ? "소득 없음"
                    : `연소득 ${activeCondition.annualIncome.toLocaleString()}만원`}{" "}
                  · 서울 {activeCondition.district} ·{" "}
                  {activeCondition.housingType === "monthly_rent"
                    ? "월세"
                    : activeCondition.housingType === "jeonse"
                      ? "전세"
                      : activeCondition.housingType === "owned"
                        ? "자가"
                        : activeCondition.housingType === "dormitory"
                          ? "기숙사"
                          : "무주택"}
                  {activeCondition.parentIncome > 0
                    ? ` · 부모소득 ${activeCondition.parentIncome.toLocaleString()}만원`
                    : ""}
                </p>
              </div>
            </div>
            <SummaryCards
              totalAmount={totalAmount}
              selectedCount={selectedCount}
              totalCount={grants.length}
              hasOptimized={hasOptimized}
            />
            {hasOptimized ? (
              <SubsidyList
                subsidies={filteredSubsidies}
                selectedSubsidies={selectedSubsidies}
                onToggle={toggleSubsidy}
                categories={CATEGORIES}
                duplicateGroups={dynamicDupGroups}
              />
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <h3>조건을 설정하고 최적조합을 탐색해보세요</h3>
                <p>
                  왼쪽 사이드바에서 조건을 입력한 후<br />
                  최적 조합 탐색 버튼을 눌러주세요.
                </p>
              </div>
            )}
          </main>
        </div>
      )}

      {currentPage === "roadmap" && (
        <div className="subpage-wrap">
          <RoadmapPage
            subsidies={filteredSubsidies}
            selectedSubsidies={selectedSubsidies}
            hasOptimized={hasOptimized}
          />
        </div>
      )}

      {currentPage === "benefits" && (
        <div className="subpage-wrap">
          <BenefitsPage
            condition={activeCondition}
            dbBenefits={extraBenefits}
          />
        </div>
      )}
    </div>
  );
}

export default DashboardPage;
