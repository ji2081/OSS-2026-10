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
import ExclusionGraphPage from "./ExclusionGraphPage";

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
  const [recommendedSelections, setRecommendedSelections] = useState({});
  const [allMappedPolicies, setAllMappedPolicies] = useState([]);
  const [roadmapData, setRoadmapData] = useState(null);

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
        culture: "culture",
        education: "education",
        employment: "employment",
        finance: "finance",
        health: "health",
        housing: "housing",
        military: "military",
        welfare: "health",
        startup: "employment",
      };

      const typeMap = {
        subsidy: "confirmed",
        interest_subsidy: "confirmed",
        savings: "confirmed",
        voucher: "utilization",
        cashback: "utilization",
        pass: "utilization",
        goods: "selective",
        loan: "selective",
        other: "selective",
      };

      const benefitCatMap = {
        culture: "culture",
        education: "employment",
        employment: "employment",
        finance: "welfare",
        health: "welfare",
        housing: "welfare",
        military: "welfare",
      };

      const mapPolicy = (p) => ({
        id: p.id,
        name: p.title,
        category: categoryMap[p.category] || "employment",
        type: typeMap[p.benefit_type] || "selective",
        benefit_type: p.benefit_type,
        amount:
          p.tiers && p.tiers.length > 0
            ? Math.round(
                (p.tiers[0].monthly_benefit * p.tiers[0].duration_months) /
                  10000,
              )
            : 0,
        apply_start: p.apply_start || null,
        apply_end: p.apply_end || null,
        is_active: p.is_active !== false,
        is_open_ended: p.is_open_ended || false,
        provider: p.host_org || "",
        exclusive_with: p.exclusive_with || [],
        warning: p.target_unemployed_only ? "미취업자" : null,
        description: p.benefit_description || "",
        documents: [],
        source_url: p.source_url,
        deadline: p.apply_end,
        duration_months:
          p.tiers && p.tiers.length > 0 ? p.tiers[0].duration_months : null,
        situational_condition: p.situational_condition || null,
      });

      const toBenefit = (p) => ({
        id: p.id,
        name: p.name,
        category: benefitCatMap[p.category] || "welfare",
        type: p.type,
        typeLabel:
          p.benefit_type === "loan"
            ? "대출"
            : p.benefit_type === "goods"
              ? "물품"
              : "서비스",
        amount: null,
        amountLabel: "별도 안내",
        provider: p.provider,
        description: p.description,
        source_url: p.source_url,
        situational_condition: p.situational_condition || null,
        tags: [],
        period: p.apply_start
          ? { start: p.apply_start, end: p.apply_end }
          : null,
        eligibility: {},
        isOneTime: false,
        isRecurring: false,
        howToApply: "해당 기관 홈페이지 또는 방문 신청",
      });

      const converted = data.selected_policies.map(mapPolicy);
      const supplementaryConverted = (data.supplementary_policies || []).map(
        mapPolicy,
      );

      const mainPolicies = converted.filter(
        (p) =>
          (p.type === "confirmed" || p.type === "utilization") &&
          p.amount &&
          p.amount > 0,
      );
      const nullAsBenefits = converted
        .filter((p) => p.type === "selective")
        .map(toBenefit);

      const suppMain = supplementaryConverted.filter(
        (p) =>
          (p.type === "confirmed" || p.type === "utilization") &&
          p.amount &&
          p.amount > 0,
      );
      const suppBenefits = supplementaryConverted
        .filter((p) => p.type === "selective")
        .map(toBenefit);

      setFilteredSubsidies([...mainPolicies, ...suppMain]);
      setAllMappedPolicies([...converted, ...supplementaryConverted]);
      console.log("allMappedPolicies:", allMappedPolicies.length);
      console.log(
        "exclusive_with 샘플:",
        [...converted, ...supplementaryConverted][0]?.exclusive_with,
      );
      console.log("id 샘플:", [...converted, ...supplementaryConverted][0]?.id);
      setExtraBenefits([...nullAsBenefits, ...suppBenefits]);

      const allPolicies = [...mainPolicies, ...suppMain];
      const newSelections = {};

      mainPolicies.forEach((s) => {
        newSelections[s.id] = true;
      });

      suppMain.forEach((s) => {
        const hasConflict = (s.exclusive_with || []).some(
          (id) => newSelections[id],
        );
        if (!hasConflict) {
          newSelections[s.id] = true;
        }
      });

      allPolicies
        .filter((s) => s.type === "confirmed" && s.amount && s.amount > 0)
        .forEach((s) => {
          const hasConflictSelected = (s.exclusive_with || []).some((id) => {
            const conflictPolicy = allPolicies.find((x) => x.id === id);
            return newSelections[id] && conflictPolicy?.type === "confirmed";
          });
          if (!hasConflictSelected) {
            newSelections[s.id] = true;
          }
        });

      setSelectedSubsidies(newSelections);
      setRecommendedSelections({ ...newSelections });
      setHasOptimized(true);

      try {
        const roadmapRes = await fetch(`${backendUrl}/policies/roadmap`, {
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
                  ? null
                  : activeCondition.annualIncome / 10000,
              is_employed: activeCondition.isEmployed,
              region: activeCondition.district || "서울",
            },
          }),
        });
        if (roadmapRes.ok) {
          setRoadmapData(await roadmapRes.json());
        }
      } catch (e) {
        console.warn("roadmap API 실패:", e);
      }

      console.log("백엔드 추천 총액:", data.total_benefit);
    } catch (err) {
      console.error("API 에러:", err);
      setFilteredSubsidies([]);
      setSelectedSubsidies({});
      setHasOptimized(true);
      alert("서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인해주세요.");
    }
  };

  const toggleSubsidy = (subsidyId) => {
    const subsidy = filteredSubsidies.find((s) => s.id === subsidyId);

    if (
      subsidy &&
      subsidy.exclusive_with &&
      subsidy.exclusive_with.length > 0
    ) {
      setSelectedSubsidies((prev) => {
        const next = { ...prev };
        subsidy.exclusive_with.forEach((id) => {
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

  // 충돌 그룹 생성 (confirmed 타입끼리만)
  const dynamicDupGroups = [];
  const processed = new Set();
  filteredSubsidies
    .filter((s) => s.type === "confirmed")
    .forEach((s) => {
      if (s.exclusive_with?.length > 0 && !processed.has(s.id)) {
        const conflictingConfirmed = s.exclusive_with.filter((id) => {
          const x = filteredSubsidies.find((p) => p.id === id);
          return x && x.type === "confirmed";
        });
        if (conflictingConfirmed.length > 0) {
          const group = [s.id, ...conflictingConfirmed];
          group.forEach((id) => processed.add(id));
          const conflictNames = conflictingConfirmed
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

  const confirmedPolicies = filteredSubsidies.filter(
    (s) => s.type === "confirmed",
  );
  const utilizationPolicies = filteredSubsidies.filter(
    (s) => s.type === "utilization",
  );

  const selectedConfirmed = confirmedPolicies.filter(
    (s) => selectedSubsidies[s.id] && s.amount && s.amount > 0,
  );
  const selectedUtilization = utilizationPolicies.filter(
    (s) => selectedSubsidies[s.id] && s.amount && s.amount > 0,
  );

  const confirmedAmount = selectedConfirmed.reduce(
    (sum, s) => sum + (s.amount || 0),
    0,
  );
  const utilizationAmount = selectedUtilization.reduce(
    (sum, s) => sum + (s.amount || 0),
    0,
  );
  const totalAmount = confirmedAmount + utilizationAmount;
  const selectedCount = selectedConfirmed.length + selectedUtilization.length;
  const grants = [...confirmedPolicies, ...utilizationPolicies].filter(
    (s) => s.amount && s.amount > 0,
  );

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
          <a
            href="#"
            className={`nav-item${currentPage === "graph" ? " active" : ""}`}
            onClick={(e) => {
              e.preventDefault();
              setCurrentPage("graph");
            }}
          >
            정책 그래프
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
              confirmedAmount={confirmedAmount}
              utilizationAmount={utilizationAmount}
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
                onResetToRecommended={() =>
                  setSelectedSubsidies({ ...recommendedSelections })
                }
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
            roadmapData={roadmapData}
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

      {currentPage === "graph" && (
        <div className="subpage-wrap">
          <ExclusionGraphPage
            selectedSubsidies={selectedSubsidies}
            hasOptimized={hasOptimized}
          />
        </div>
      )}
    </div>
  );
}

export default DashboardPage;
