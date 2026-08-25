import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import SummaryCards from "../components/SummaryCards";
import SubsidyList from "../components/SubsidyList";
import ConditionQuestionsCard from "../components/ConditionQuestionsCard";
import RoadmapPage from "./RoadmapPage";
import BenefitsPage from "./BenefitsPage";
import logoImg from "../logo.png";
import "./DashboardPage.css";
import { CATEGORIES } from "../data/subsidies";
import ExclusionGraphPage from "./ExclusionGraphPage";
import RequestFeedback from "../components/RequestFeedback";

const EMPTY_SELECTIONS = {};

async function readResponse(response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      data?.detail || data?.message || `요청에 실패했습니다. (${response.status})`;
    throw new Error(typeof message === "string" ? message : "입력값을 확인해주세요.");
  }
  return data;
}

function getRequestErrorMessage(error) {
  if (error instanceof TypeError || error?.name === "AbortError") {
    return "서버에 연결할 수 없습니다. 네트워크와 백엔드 실행 상태를 확인해주세요.";
  }
  return error?.message || "요청 처리 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.";
}

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
  const activeSetIdRef = useRef(activeSetId);
  activeSetIdRef.current = activeSetId;
  const [nextId, setNextId] = useState(2);
  const [roadmapRetryCount, setRoadmapRetryCount] = useState(0);
  const activeCondition =
    conditionSets.find((s) => s.id === activeSetId) || conditionSets[0];

  const addConditionSet = () => {
    setConditionSets((prev) => {
      if (prev.length >= 4) return prev;
      const newSet = { id: nextId, name: "", ...defaultCondition };
      return [...prev, newSet];
    });
    setActiveSetId(nextId);
    setNextId((prev) => prev + 1);
  };

  const removeConditionSet = (id) => {
    if (conditionSets.length <= 1) return;
    const filtered = conditionSets.filter((s) => s.id !== id);
    setConditionSets(filtered);
    if (activeSetId === id) setActiveSetId(filtered[0].id);
  };
  const updateCondition = (field, value) => {
    setConditionSets((prev) =>
      prev.map((s) =>
        s.id === activeSetIdRef.current ? { ...s, [field]: value } : s,
      ),
    );
  };
  const renameConditionSet = (id, newName) => {
    setConditionSets((prev) =>
      prev.map((s) => (s.id === id ? { ...s, name: newName } : s)),
    );
  };

  // 세트별 결과 저장
  const [resultsBySet, setResultsBySet] = useState({});
  const r = resultsBySet[activeSetId] || {};
  const selectedSubsidies = r.selectedSubsidies || EMPTY_SELECTIONS;
  const filteredSubsidies = r.filteredSubsidies || [];
  const hasOptimized = r.hasOptimized || false;
  const extraBenefits = r.extraBenefits || [];
  const recommendedSelections = r.recommendedSelections || {};
  const roadmapData = r.roadmapData || null;
  const profilePayload = r.profilePayload || null;
  const optimizeStatus = r.optimizeStatus || "idle";
  const optimizeError = r.optimizeError || "";
  const roadmapStatus = r.roadmapStatus || "idle";
  const roadmapError = r.roadmapError || "";
  const pendingQuestions = r.pendingQuestions || [];

  const updateResult = useCallback((updates) => {
    setResultsBySet((prev) => ({
      ...prev,
      [activeSetIdRef.current]: {
        ...(prev[activeSetIdRef.current] || {}),
        ...updates,
      },
    }));
  }, []);

  const handleOptimize = async () => {
    const annualIncome = Number(activeCondition.annualIncome);
    const parentIncome = Number(activeCondition.parentIncome);
    if (
      !Number.isFinite(activeCondition.age) ||
      activeCondition.age < 19 ||
      activeCondition.age > 39
    ) {
      updateResult({ optimizeStatus: "error", optimizeError: "나이는 만 19세부터 39세까지 입력해주세요." });
      return;
    }
    if (!Number.isFinite(annualIncome) || annualIncome < 0 || annualIncome > 10000) {
      updateResult({ optimizeStatus: "error", optimizeError: "연소득은 0만원부터 10,000만원까지 입력해주세요." });
      return;
    }
    if (!Number.isFinite(parentIncome) || parentIncome < 0 || parentIncome > 30000) {
      updateResult({ optimizeStatus: "error", optimizeError: "부모소득은 0만원부터 30,000만원까지 입력해주세요." });
      return;
    }
    if (!activeCondition.district) {
      updateResult({ optimizeStatus: "error", optimizeError: "거주 구를 선택해주세요." });
      return;
    }

    updateResult({ optimizeStatus: "loading", optimizeError: "", roadmapStatus: "idle", roadmapError: "" });
    try {
      const backendUrl = process.env.REACT_APP_API_URL || "https://oss-2026-10-production.up.railway.app";

      const income_level =
        activeCondition.annualIncome === 0
          ? null
          : activeCondition.annualIncome / 3077;

      const payload = {
        age: activeCondition.age,
        income_level,
        is_employed: activeCondition.isEmployed,
        is_basic_livelihood: activeCondition.isBasicLivelihood,
        is_next_tier: activeCondition.isNextTier,
        region: "서울",
        sub_region: activeCondition.district,
      };
      updateResult({ profilePayload: payload });

      const res = await fetch(`${backendUrl}/policies/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ profile: payload, min_confidence: 0.5 }),
      });
      const data = await readResponse(res);
      if (!Array.isArray(data?.selected_policies)) {
        throw new Error("서버 응답 형식이 올바르지 않습니다.");
      }
      console.log("백엔드 응답:", data);

      const categoryMap = {
        culture: "culture",
        education: "education",
        employment: "employment",
        finance: "finance",
        health: "health",
        housing: "housing",
        military: "military",
        rights: "rights",
        scholarship: "scholarship",
        startup: "startup",
        welfare: "welfare",
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
        amount: p.resolved_tier
          ? Math.round(
              (p.resolved_tier.monthly_benefit *
                p.resolved_tier.duration_months) /
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
        duration_months: p.resolved_tier
          ? p.resolved_tier.duration_months
          : null,
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

      updateResult({
        filteredSubsidies: [...mainPolicies, ...suppMain],
        allMappedPolicies: [...converted, ...supplementaryConverted],
        extraBenefits: [...nullAsBenefits, ...suppBenefits],
      });

      const allPolicies = [...mainPolicies, ...suppMain];
      const newSelections = {};

      mainPolicies.forEach((s) => {
        newSelections[s.id] = s.category !== "scholarship";
      });

      suppMain.forEach((s) => {
        const hasConflict = (s.exclusive_with || []).some(
          (id) => newSelections[id],
        );
        if (!hasConflict && s.category !== "scholarship") {
          newSelections[s.id] = true;
        }
      });

      allPolicies
        .filter(
          (s) =>
            s.type === "confirmed" &&
            s.amount &&
            s.amount > 0 &&
            s.category !== "scholarship",
        )
        .forEach((s) => {
          const hasConflictSelected = (s.exclusive_with || []).some((id) => {
            const conflictPolicy = allPolicies.find((x) => x.id === id);
            return newSelections[id] && conflictPolicy?.type === "confirmed";
          });
          if (!hasConflictSelected) {
            newSelections[s.id] = true;
          }
        });

      updateResult({
        selectedSubsidies: newSelections,
        recommendedSelections: { ...newSelections },
        hasOptimized: true,
        optimizeStatus:
          converted.length + supplementaryConverted.length === 0 ? "empty" : "success",
        optimizeError: "",
        pendingQuestions: data.pending_questions || [],
      });

      // /roadmap API 호출
      try {
        updateResult({ roadmapStatus: "loading", roadmapError: "", roadmapData: null });
        const roadmapRes = await fetch(`${backendUrl}/policies/roadmap`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
          body: JSON.stringify({
            profile: payload,
            selected_policy_ids: data.selected_policies.map((p) => p.id),
          }),
        });
        const nextRoadmap = await readResponse(roadmapRes);
        const hasRoadmap = Array.isArray(nextRoadmap?.phases) && nextRoadmap.phases.length > 0;
        updateResult({
          roadmapData: nextRoadmap,
          roadmapStatus: hasRoadmap ? "success" : "empty",
          roadmapError: "",
        });
      } catch (e) {
        console.warn("roadmap API 실패:", e);
        updateResult({ roadmapData: null, roadmapStatus: "error", roadmapError: e.message });
      }

      console.log("백엔드 추천 총액:", data.total_benefit);
    } catch (err) {
      console.error("API 에러:", err);
      updateResult({
        filteredSubsidies: [],
        selectedSubsidies: {},
        extraBenefits: [],
        allMappedPolicies: [],
        hasOptimized: false,
        optimizeStatus: "error",
        optimizeError: getRequestErrorMessage(err),
      });
    }
  };

  const handleAnswerTag = async (tag, value) => {
    const backendUrl =
      process.env.REACT_APP_API_URL ||
      "https://oss-2026-10-production.up.railway.app";
    try {
      await fetch(`${backendUrl}/profiles/me/condition-tags`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ [tag]: value }),
      });
    } catch (e) {
      console.warn("조건 답변 저장 실패:", e);
    }
    // 답변에 따라 결과(포함 여부)가 바뀔 수 있으니 다시 최적화를 돌린다.
    await handleOptimize();
  };

  const toggleSubsidy = (subsidyId) => {
    const subsidy = filteredSubsidies.find((s) => s.id === subsidyId);

    if (
      subsidy &&
      subsidy.exclusive_with &&
      subsidy.exclusive_with.length > 0
    ) {
      const next = { ...selectedSubsidies };
      subsidy.exclusive_with.forEach((id) => {
        next[id] = false;
      });
      next[subsidyId] = !selectedSubsidies[subsidyId];
      updateResult({ selectedSubsidies: next });
      return;
    }

    updateResult({
      selectedSubsidies: {
        ...selectedSubsidies,
        [subsidyId]: !selectedSubsidies[subsidyId],
      },
    });
  };

  useEffect(() => {
    if (currentPage !== "roadmap" || !hasOptimized || !profilePayload) return;
    const selected = Object.keys(selectedSubsidies).filter(
      (id) => selectedSubsidies[id],
    );
    if (!selected.length) return;
    const backendUrl = process.env.REACT_APP_API_URL || "https://oss-2026-10-production.up.railway.app";
    updateResult({ roadmapStatus: "loading", roadmapError: "", roadmapData: null });
    fetch(`${backendUrl}/policies/roadmap`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
      body: JSON.stringify({
        profile: profilePayload,
        selected_policy_ids: selected,
      }),
    })
      .then(readResponse)
      .then((d) => {
        const hasRoadmap = Array.isArray(d?.phases) && d.phases.length > 0;
        updateResult({ roadmapData: d, roadmapStatus: hasRoadmap ? "success" : "empty" });
      })
      .catch((e) => {
        console.warn("roadmap 재계산 실패:", e);
        updateResult({ roadmapData: null, roadmapStatus: "error", roadmapError: e.message });
      });
  }, [currentPage, hasOptimized, profilePayload, selectedSubsidies, updateResult, roadmapRetryCount]);

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
          <img src={logoImg} alt="돈다바짜" style={{ width: 24, height: 24 }} />
          <h1>돈다바짜</h1>
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

      <RequestFeedback
        status={optimizeStatus}
        title={optimizeStatus === "loading" ? "지원 정책 분석 중" : "분석에 실패했습니다"}
        message={optimizeStatus === "loading" ? "잠시만 기다려주세요." : optimizeError}
        onRetry={handleOptimize}
        onDismiss={() => updateResult({ optimizeStatus: "idle", optimizeError: "" })}
      />

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
            isOptimizing={optimizeStatus === "loading"}
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
            {hasOptimized && (
              <ConditionQuestionsCard
                questions={pendingQuestions}
                onAnswer={handleAnswerTag}
              />
            )}
            <SummaryCards
              totalAmount={totalAmount}
              confirmedAmount={confirmedAmount}
              utilizationAmount={utilizationAmount}
              selectedCount={selectedCount}
              totalCount={grants.length}
              hasOptimized={hasOptimized}
            />
            {optimizeStatus === "empty" ? (
              <RequestState icon="∅" title="조건에 맞는 결과가 없습니다" message="조건을 변경한 뒤 다시 탐색해보세요." />
            ) : hasOptimized && filteredSubsidies.length === 0 ? (
              <RequestState
                icon="∅"
                title="표시할 지원금 결과가 없습니다"
                message={extraBenefits.length > 0 ? "알짜배기 정보에서 추가 혜택을 확인해보세요." : "조건을 변경한 뒤 다시 탐색해보세요."}
              />
            ) : hasOptimized ? (
              <SubsidyList
                subsidies={filteredSubsidies}
                selectedSubsidies={selectedSubsidies}
                onToggle={toggleSubsidy}
                categories={CATEGORIES}
                duplicateGroups={dynamicDupGroups}
                onResetToRecommended={() =>
                  updateResult({
                    selectedSubsidies: { ...recommendedSelections },
                  })
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
            requestStatus={roadmapStatus}
            errorMessage={roadmapError}
            onRetry={() => setRoadmapRetryCount((count) => count + 1)}
            onDismissError={() => updateResult({ roadmapStatus: "idle", roadmapError: "" })}
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

function RequestState({ icon, title, message, onRetry }) {
  return (
    <div className="empty-state" role={title.includes("실패") ? "alert" : "status"}>
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{message}</p>
      {onRetry && <button className="state-retry-button" onClick={onRetry}>다시 시도</button>}
    </div>
  );
}

export default DashboardPage;
