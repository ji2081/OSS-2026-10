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
