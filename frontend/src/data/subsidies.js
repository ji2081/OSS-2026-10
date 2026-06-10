export const DISTRICTS = [
  "강남구",
  "강동구",
  "강북구",
  "강서구",
  "관악구",
  "광진구",
  "구로구",
  "금천구",
  "노원구",
  "도봉구",
  "동대문구",
  "동작구",
  "마포구",
  "서대문구",
  "서초구",
  "성동구",
  "성북구",
  "송파구",
  "양천구",
  "영등포구",
  "용산구",
  "은평구",
  "종로구",
  "중구",
  "중랑구",
];
export const EDUCATION_OPTIONS = [
  { value: "high_school", label: "고졸" },
  { value: "university", label: "대학재학중" },
  { value: "leave", label: "휴학" },
  { value: "graduated", label: "대졸" },
  { value: "grad_school", label: "대학원" },
];
export const HOUSING_OPTIONS = [
  { value: "monthly_rent", label: "월세 (임차)" },
  { value: "jeonse", label: "전세" },
  { value: "owned", label: "자가" },
  { value: "dormitory", label: "기숙사" },
  { value: "homeless", label: "무주택" },
];
export const CATEGORIES = {
  employment: { key: "employment", label: "취업·교육", color: "#FB8C00" },
  housing: { key: "housing", label: "주거", color: "#43A047" },
  finance: { key: "finance", label: "금융·자산", color: "#007AFF" },
  health: { key: "health", label: "건강·복지", color: "#00BCD4" },
  culture: { key: "culture", label: "문화", color: "#FF375F" },
  military: { key: "military", label: "군장병", color: "#5AC8FA" },
  education: { key: "education", label: "교육", color: "#8E24AA" },
  rights: { key: "rights", label: "권리·법률", color: "#FF6B35" },
  scholarship: { key: "scholarship", label: "장학금", color: "#E91E63" },
  startup: { key: "startup", label: "창업", color: "#FB8C00" },
  welfare: { key: "welfare", label: "복지", color: "#5AC8FA" },
};

export function checkEligibility(policy, condition) {
  const r = policy.eligibility;
  if (!r) return true;
  if (r.minAge && condition.age < r.minAge) return false;
  if (r.maxAge && condition.age > r.maxAge) return false;
  // 본인소득: 0이면 소득없음이므로 통과, 입력값이 있을때만 체크
  if (
    r.maxIncome !== undefined &&
    condition.annualIncome > 0 &&
    condition.annualIncome > r.maxIncome
  )
    return false;
  // 부모소득: 0이면 소득없음이므로 통과, 입력값이 있을때만 체크
  if (
    r.maxParentIncome !== undefined &&
    condition.parentIncome > 0 &&
    condition.parentIncome > r.maxParentIncome
  )
    return false;
  if (r.requireEmployed && !condition.isEmployed) return false;
  if (r.requireUnemployed && condition.isEmployed) return false;
  if (r.requireBelow150Median && !condition.isBelow150Median) return false;
  if (r.requireStudentLoan && !condition.hasStudentLoan) return false;
  if (r.housingTypes && !r.housingTypes.includes(condition.housingType))
    return false;
  if (
    r.excludeEducation &&
    r.excludeEducation.includes(condition.educationStatus)
  )
    return false;
  return true;
}

export const MOCK_SUBSIDIES = [
  {
    id: "youth-allowance",
    name: "서울시 청년수당",
    category: "living",
    type: "grant",
    amount: 300,
    startDate: "2025-07",
    endDate: "2025-12",
    provider: "서울시",
    isDuplicate: true,
    duplicateGroup: "living-a",
    duplicateWith: ["employment-support"],
    warning: "미취업자",
    description:
      "미취업 청년 월 50만원, 최대 6개월. 구직활동 지원 프로그램(멘토링, 특강) 포함. 제로페이 포인트로 지급.",
    documents: ["주민등록등본", "최종학력 증명서", "건강보험료 납부확인서"],
    applyUrl: "https://youth.seoul.go.kr",
    deadline: "2025-06-12",
    eligibility: {
      minAge: 19,
      maxAge: 34,
      requireUnemployed: true,
      requireBelow150Median: true,
      excludeEducation: ["university", "leave", "grad_school"],
    },
  },
  {
    id: "rent-support-national",
    name: "청년월세지원 (국토부)",
    category: "realestate",
    type: "grant",
    amount: 240,
    startDate: "2025-01",
    endDate: "2026-12",
    provider: "국토교통부",
    isDuplicate: true,
    duplicateGroup: "rent-a",
    duplicateWith: ["rent-support-seoul"],
    warning: "부모소득 연동",
    description:
      "월세 거주 청년 월 최대 20만원, 24개월. 중위소득 60% 이하, 부모소득 연 1억 미만.",
    documents: [
      "주민등록등본",
      "임대차계약서",
      "소득증빙서류",
      "가족관계증명서",
    ],
    applyUrl: "https://www.bokjiro.go.kr",
    deadline: null,
    eligibility: {
      minAge: 19,
      maxAge: 34,
      housingTypes: ["monthly_rent"],
      requireBelow150Median: true,
      maxParentIncome: 10000,
    },
  },
  {
    id: "rent-support-seoul",
    name: "청년월세지원 (서울시)",
    category: "realestate",
    type: "grant",
    amount: 240,
    startDate: "2025-06",
    endDate: "2026-05",
    provider: "서울시",
    isDuplicate: true,
    duplicateGroup: "rent-a",
    duplicateWith: ["rent-support-national"],
    warning: "부모소득 연동",
    description:
      "서울 거주 1인가구 월 최대 20만원, 12개월. 부모소득 연 1억 미만. 국토부 종료 후 순차 가능.",
    documents: [
      "주민등록등본",
      "임대차계약서",
      "건강보험료 납부확인서",
      "가족관계증명서",
    ],
    applyUrl: "https://housing.seoul.go.kr",
    deadline: "2025-06-24",
    eligibility: {
      minAge: 19,
      maxAge: 39,
      housingTypes: ["monthly_rent"],
      requireBelow150Median: true,
      maxParentIncome: 10000,
    },
  },
  {
    id: "tomorrow-savings",
    name: "청년내일채움공제",
    category: "employment",
    type: "grant",
    amount: 1200,
    startDate: "2025-01",
    endDate: "2026-12",
    provider: "고용노동부",
    isDuplicate: true,
    duplicateGroup: "employ-a",
    duplicateWith: ["employment-support"],
    warning: "재직자 한정",
    description:
      "중소기업 재직 청년. 2년간 본인 400만원 적립 시 정부+기업 800만원 추가. 총 1,200만원.",
    documents: ["재직증명서", "근로계약서", "4대보험 가입확인서"],
    applyUrl: "https://www.work.go.kr/youngtomorrow",
    deadline: null,
    eligibility: { minAge: 15, maxAge: 34, requireEmployed: true },
  },
  {
    id: "employment-support",
    name: "국민취업지원제도",
    category: "employment",
    type: "grant",
    amount: 300,
    startDate: "2025-01",
    endDate: "2025-06",
    provider: "고용노동부",
    isDuplicate: true,
    duplicateGroup: "employ-a",
    duplicateWith: ["tomorrow-savings"],
    warning: "미취업자",
    description:
      "구직촉진수당 월 50만원 x 6개월. 취업컨설팅, 직업훈련, 일경험 프로그램 포함.",
    documents: ["구직등록확인증", "소득증빙서류", "주민등록등본"],
    applyUrl: "https://www.kua.go.kr",
    deadline: null,
    eligibility: { minAge: 15, maxAge: 34, requireUnemployed: true },
  },
  {
    id: "loan-interest",
    name: "학자금대출 이자지원",
    category: "employment",
    type: "grant",
    amount: 30,
    startDate: "2025-01",
    endDate: "2025-12",
    provider: "서울시",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: "학자금대출 보유자",
    description: "한국장학재단 학자금대출 이자를 소득분위별 지원. 반기별 신청.",
    documents: ["장학재단 이자납부확인서", "주민등록등본"],
    applyUrl: "https://youth.seoul.go.kr",
    deadline: "2025-09-11",
    eligibility: { requireStudentLoan: true },
  },
  {
    id: "exam-fee",
    name: "자격증 응시료 지원",
    category: "employment",
    type: "grant",
    amount: 10,
    startDate: "2025-01",
    endDate: "2025-12",
    provider: "자치구",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: "구마다 상이",
    description: "어학·국가자격시험 응시료 지원. 미취업 청년, 자치구별 운영.",
    documents: ["응시료 영수증", "주민등록등본"],
    applyUrl: null,
    deadline: null,
    eligibility: { minAge: 19, maxAge: 39, requireUnemployed: true },
  },
  {
    id: "transport-support",
    name: "청년교통비 지원",
    category: "transport",
    type: "grant",
    amount: 10,
    startDate: "2025-01",
    endDate: "2025-12",
    provider: "서울시",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: "만 19~24세",
    description: "대중교통 이용금액 20% 마일리지, 연 최대 10만원.",
    documents: ["교통카드 등록"],
    applyUrl: "https://youth.seoul.go.kr",
    deadline: null,
    eligibility: { minAge: 19, maxAge: 24 },
  },
  {
    id: "kpass",
    name: "K-패스 교통비 환급",
    category: "transport",
    type: "grant",
    amount: 10,
    startDate: "2025-01",
    endDate: "2025-12",
    provider: "국토교통부",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: null,
    description: "대중교통 월 15회 이상 이용 시 청년 30% 환급.",
    documents: ["K-패스 앱 가입"],
    applyUrl: "https://www.k-pass.go.kr",
    deadline: null,
    eligibility: { minAge: 19, maxAge: 34 },
  },
  // 적금
  {
    id: "hope-savings",
    name: "희망두배청년통장",
    type: "savings",
    category: "asset",
    amount: 1080,
    startDate: "2025-06",
    endDate: "2028-05",
    provider: "서울시",
    isDuplicate: true,
    duplicateGroup: "savings-a",
    duplicateWith: ["nael-savings"],
    warning: "부모소득 연동",
    description:
      "월 15만원 저축 시 서울시 100% 매칭. 최대 1,080만원. 부모소득 연 1억 미만.",
    documents: ["근로증빙서류", "주민등록초본", "가족관계증명서"],
    applyUrl: "https://account.welfare.seoul.kr",
    deadline: "2025-06-20",
    eligibility: {
      minAge: 18,
      maxAge: 34,
      requireEmployed: true,
      maxIncome: 3060,
      maxParentIncome: 10000,
    },
  },
  {
    id: "nael-savings",
    name: "청년내일저축계좌",
    type: "savings",
    category: "asset",
    amount: 1440,
    startDate: "2025-05",
    endDate: "2028-04",
    provider: "보건복지부",
    isDuplicate: true,
    duplicateGroup: "savings-a",
    duplicateWith: ["hope-savings"],
    warning: "저소득 근로청년",
    description: "월 10만원 저축 시 정부 10~30만원 매칭. 최대 1,440만원.",
    documents: ["재직증명서", "소득증빙서류"],
    applyUrl: "https://www.bokjiro.go.kr",
    deadline: "2025-05-21",
    eligibility: {
      minAge: 15,
      maxAge: 39,
      requireEmployed: true,
      requireBelow150Median: true,
    },
  },
  {
    id: "doyak",
    name: "청년도약계좌",
    type: "savings",
    category: "asset",
    amount: 5000,
    startDate: "2025-01",
    endDate: "2029-12",
    provider: "금융위원회",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: "2025년 말 마감",
    description:
      "월 최대 70만원 납입, 5년 만기. 정부기여금+비과세, 최대 5,000만원.",
    documents: ["소득금액증명원"],
    applyUrl: "https://ylaccount.kinfa.or.kr",
    deadline: "2025-12-31",
    eligibility: { minAge: 19, maxAge: 34, maxIncome: 7500 },
  },
  // 대출
  {
    id: "jeonse-loan",
    name: "청년 전세자금 대출",
    type: "loan",
    category: "realestate",
    amount: null,
    startDate: "2025-01",
    endDate: "2026-12",
    provider: "국토교통부",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: null,
    description: "전세보증금 최대 2억원, 연 1.8~2.4% 저금리.",
    documents: ["임대차계약서", "주민등록등본", "소득증빙서류"],
    applyUrl: "https://nhuf.molit.go.kr",
    deadline: null,
    eligibility: {
      minAge: 19,
      maxAge: 34,
      housingTypes: ["jeonse"],
      maxIncome: 5000,
    },
  },
  {
    id: "deposit-interest",
    name: "청년임차보증금 이자지원",
    type: "loan",
    category: "realestate",
    amount: null,
    startDate: "2025-01",
    endDate: "2032-12",
    provider: "서울시",
    isDuplicate: false,
    duplicateGroup: null,
    duplicateWith: [],
    warning: "생애 1회",
    description: "임차보증금 최대 2억원 대출, 이자 최대 3% 서울시 지원.",
    documents: ["임대차계약서", "주민등록등본"],
    applyUrl: "https://housing.seoul.go.kr",
    deadline: null,
    eligibility: { minAge: 19, maxAge: 39, maxIncome: 4000 },
  },
];

export const DUPLICATE_GROUPS = [
  {
    id: "living-a",
    name: "생활지원 중복 제한",
    items: ["youth-allowance", "employment-support"],
    recommendedId: "youth-allowance",
    reason:
      "청년수당은 서울시 성장지원 프로그램(멘토링, 특강)이 추가 제공됩니다.",
  },
  {
    id: "rent-a",
    name: "월세지원 중복 제한",
    items: ["rent-support-national", "rent-support-seoul"],
    recommendedId: "rent-support-national",
    reason:
      "국토부 먼저 수혜 후, 종료 시 서울시로 순차 신청하면 총 36개월 가능.",
  },
  {
    id: "employ-a",
    name: "취업지원 중복 제한",
    items: ["tomorrow-savings", "employment-support"],
    recommendedId: "tomorrow-savings",
    reason:
      "내일채움공제 1,200만원 vs 국민취업지원 300만원. 총 수혜액 4배 차이.",
  },
  {
    id: "savings-a",
    name: "자산형성 중복 제한",
    items: ["hope-savings", "nael-savings"],
    recommendedId: "nael-savings",
    reason:
      "내일저축계좌는 정부매칭 최대 30만원/월로 희망두배(15만원/월) 대비 높음.",
  },
];

export const OPTIMAL_COMBINATION = [
  "youth-allowance",
  "rent-support-national",
  "tomorrow-savings",
  "transport-support",
  "kpass",
];

export function mapPolicyToSubsidy(policy) {
  const typeMap = {
    subsidy: "grant",
    cashback: "grant",
    pass: "grant",
    loan: "loan",
    interest_subsidy: "loan",
    savings: "savings",
    voucher: "service",
    goods: "service",
    service: "service",
    other: "service",
  };
  return {
    id: policy.id,
    name: policy.title,
    category: policy.category,
    type: typeMap[policy.benefit_type] || "grant",
    amount: policy.total_benefit
      ? Math.round(policy.total_benefit / 10000)
      : null,
    provider: policy.host_org,
    startDate: policy.apply_start?.slice(0, 7),
    endDate: policy.apply_end?.slice(0, 7),
    description: policy.benefit_description,
    duplicateGroup: policy.exclusive_with?.length
      ? policy.exclusive_with[0]
      : null,
    isDuplicate: policy.exclusive_with?.length > 0,
    duplicateWith: policy.exclusive_with || [],
    warning: null,
    eligibility: {
      minAge: policy.age_min || undefined,
      maxAge: policy.age_max || undefined,
      maxIncome: policy.income_limit || undefined,
      requireUnemployed: policy.target_unemployed_only || false,
    },
    applyUrl: policy.source_url || null,
  };
}

export function mapPolicyToBenefit(policy) {
  const catMap = {
    health: "welfare",
    welfare: "welfare",
    culture: "culture",
    employment: "employment",
    education: "employment",
    startup: "employment",
    housing: "welfare",
    finance: "welfare",
  };
  return {
    id: policy.id,
    name: policy.title,
    category: catMap[policy.category] || "welfare",
    type: policy.benefit_type,
    typeLabel: policy.benefit_type,
    amount: policy.total_benefit
      ? Math.round(policy.total_benefit / 10000)
      : null,
    amountLabel: policy.total_benefit
      ? `최대 ${Math.round(policy.total_benefit / 10000).toLocaleString()}만원`
      : "별도 안내",
    provider: policy.host_org,
    description: policy.benefit_description,
    applyUrl: policy.source_url || null,
    tags: [policy.category, policy.benefit_type].filter(Boolean),
    period: policy.apply_start
      ? {
          start: policy.apply_start.slice(0, 7),
          end: policy.apply_end?.slice(0, 7),
        }
      : null,
    eligibility: {},
    isOneTime: false,
    isRecurring: false,
    howToApply: "해당 기관 홈페이지 또는 방문 신청",
  };
}
export function getApplicationStatus(policy) {
  const today = new Date();
  const start = policy.apply_start ? new Date(policy.apply_start) : null;
  const end = policy.apply_end ? new Date(policy.apply_end) : null;

  if (policy.is_active === false)
    return { label: "종료", color: "#999", bg: "#F0F0F0" };
  if (policy.is_open_ended)
    return { label: "상시", color: "#2196F3", bg: "#E3F2FD" };
  if (!start && !end) return { label: "상시", color: "#2196F3", bg: "#E3F2FD" };
  if (start && start > today)
    return { label: "예정", color: "#FF9800", bg: "#FFF3E0", dashed: true };
  if (start && end && start <= today && end >= today) {
    const daysLeft = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
    if (daysLeft <= 7)
      return { label: "마감임박", color: "#F44336", bg: "#FFEBEE" };
    return { label: "모집중", color: "#4CAF50", bg: "#E8F5E9" };
  }
  return { label: "종료", color: "#999", bg: "#F0F0F0" };
}
