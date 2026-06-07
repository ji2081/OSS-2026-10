import { useState, useMemo, useEffect } from "react";
import "./ExclusionGraphPage.css";

const CATEGORY_COLORS = {
  housing: "#43A047",
  realestate: "#43A047",
  employment: "#FB8C00",
  education: "#8E24AA",
  finance: "#007AFF",
  asset: "#007AFF",
  culture: "#FF375F",
  health: "#00BCD4",
  welfare: "#5AC8FA",
  transport: "#8E24AA",
  startup: "#FB8C00",
  living: "#E53935",
  military: "#78909C",
  scholarship: "#E91E63",
  rights: "#FF6B35",
};

const CATEGORY_LABELS = {
  employment: "취업·교육",
  housing: "주거",
  finance: "금융·자산",
  health: "건강·복지",
  culture: "문화",
  military: "군장병",
  education: "교육·장학",
  scholarship: "장학",
  welfare: "복지",
  rights: "권리·법률",
};

const NODE_W = 130;
const NODE_H = 52;
const COL_GAP = 24;
const ROW_GAP = 18;
const SECTION_GAP = 40;
const PADDING = 32;

function layoutNodes(allPolicies, selectedSubsidies) {
  const byCategory = {};
  allPolicies.forEach((s) => {
    const cat = s.category || "etc";
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(s);
  });

  const catKeys = Object.keys(byCategory);
  const allNodes = [];
  let x = PADDING;
  let y = PADDING;
  let rowMaxH = 0;
  const sectionWidth = 560;

  catKeys.forEach((cat, idx) => {
    const items = byCategory[cat];
    const cols = Math.min(3, items.length);
    const rows = Math.ceil(items.length / cols);
    const sHeight = rows * (NODE_H + ROW_GAP) - ROW_GAP;

    if (idx % 2 === 0 && idx !== 0) {
      y += rowMaxH + SECTION_GAP + 32;
      x = PADDING;
      rowMaxH = 0;
    }

    items.forEach((s, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      allNodes.push({
        ...s,
        name: s.title || s.name,
        amount:
          s.tiers && s.tiers.length > 0
            ? Math.round(
                (s.tiers[0].monthly_benefit * s.tiers[0].duration_months) /
                  10000,
              )
            : s.amount || 0,
        exclusive_with: s.exclusive_with || [],
        isSelected: !!selectedSubsidies?.[s.id],
        x: x + col * (NODE_W + COL_GAP) + NODE_W / 2,
        y: y + 28 + row * (NODE_H + ROW_GAP) + NODE_H / 2,
        cat,
      });
    });

    if (idx % 2 === 0) {
      x += sectionWidth;
    } else {
      x = PADDING;
    }
    rowMaxH = Math.max(rowMaxH, sHeight + 28);
  });

  const maxX = Math.max(...allNodes.map((n) => n.x)) + NODE_W / 2 + PADDING;
  const maxY = Math.max(...allNodes.map((n) => n.y)) + NODE_H / 2 + PADDING;

  return { nodes: allNodes, totalW: maxX, totalH: maxY, byCategory };
}

function ExclusionGraphPage({ selectedSubsidies, hasOptimized }) {
  const [hoveredId, setHoveredId] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [allPolicies, setAllPolicies] = useState([]);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const backendUrl = `http://${window.location.hostname}:8000`;
        let all = [];
        let skip = 0;
        while (true) {
          const res = await fetch(
            `${backendUrl}/policies/?limit=100&skip=${skip}`,
          );
          const data = await res.json();
          if (!Array.isArray(data) || data.length === 0) break;
          all = [...all, ...data];
          if (data.length < 100) break;
          skip += 100;
        }
        all.forEach((p) => {
          (p.exclusive_with || []).forEach((tid) => {
            const target = all.find((x) => x.id === tid);
            if (target && !(target.exclusive_with || []).includes(p.id)) {
              target.exclusive_with = [...(target.exclusive_with || []), p.id];
            }
          });
        });
        setAllPolicies(all);
      } catch (err) {
        console.error("정책 로드 실패:", err);
      }
    };
    fetchAll();
  }, []);

  const { nodes, totalW, totalH, byCategory } = useMemo(
    () => layoutNodes(allPolicies, selectedSubsidies || {}),
    [allPolicies, selectedSubsidies],
  );

  const nodeMap = useMemo(() => {
    const m = {};
    nodes.forEach((n) => {
      m[n.id] = n;
    });
    return m;
  }, [nodes]);

  const links = useMemo(() => {
    const result = [];
    const seen = new Set();
    nodes.forEach((n) => {
      (n.exclusive_with || []).forEach((tid) => {
        if (nodeMap[tid]) {
          const key = [n.id, tid].sort().join("|");
          if (!seen.has(key)) {
            seen.add(key);
            result.push({ s: n, t: nodeMap[tid] });
          }
        }
      });
    });
    return result;
  }, [nodes, nodeMap]);

  const hoveredExIds = useMemo(() => {
    const s = new Set();
    if (!hoveredId) return s;
    s.add(hoveredId);
    const n = nodeMap[hoveredId];
    if (n) (n.exclusive_with || []).forEach((id) => s.add(id));
    return s;
  }, [hoveredId, nodeMap]);

  if (!hasOptimized || allPolicies.length === 0) {
    return (
      <div className="graph-page">
        <div className="graph-empty">
          <div className="graph-empty-icon">🕸️</div>
          <h3>
            {!hasOptimized
              ? "먼저 최적 조합을 탐색해주세요"
              : "정책 데이터 로딩 중..."}
          </h3>
          <p>대시보드에서 조건을 설정하고 "최적 조합 탐색"을 눌러주세요.</p>
        </div>
      </div>
    );
  }

  const totalExclusions = new Set();
  links.forEach((l) => totalExclusions.add(`${l.s.id}|${l.t.id}`));

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div>
          <h2>배타 관계 그래프</h2>
        </div>
        <div className="graph-stats">
          <div className="gstat">
            <span className="gstat-num">{allPolicies.length}</span>
            <span className="gstat-label">정책</span>
          </div>
          <div className="gstat">
            <span className="gstat-num">{totalExclusions.size}</span>
            <span className="gstat-label">배타 관계</span>
          </div>
          <div className="gstat">
            <span className="gstat-num">
              {nodes.filter((n) => n.isSelected).length}
            </span>
            <span className="gstat-label">선택됨</span>
          </div>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-rect selected-r" />
          <span>최적 선택 정책</span>
        </div>
        <div className="legend-item">
          <span className="legend-rect unselected-r" />
          <span>미선택 정책</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" />
          <span>중복 수급 불가</span>
        </div>
        <div className="legend-item">
          <span style={{ fontSize: 11, color: "#888" }}>
            노드 클릭 시 상세 정보
          </span>
        </div>
      </div>

      <div className="graph-container eg-scroll">
        <svg
          width={Math.max(totalW, 800)}
          height={totalH}
          onMouseLeave={() => setHoveredId(null)}
        >
          {Object.entries(byCategory).map(([cat]) => {
            const catNodes = nodes.filter((n) => n.cat === cat);
            if (catNodes.length === 0) return null;
            const xs = catNodes.map((n) => n.x);
            const ys = catNodes.map((n) => n.y);
            const minX = Math.min(...xs) - NODE_W / 2 - 10;
            const minY = Math.min(...ys) - NODE_H / 2 - 28;
            const maxX = Math.max(...xs) + NODE_W / 2 + 10;
            const maxY = Math.max(...ys) + NODE_H / 2 + 10;
            const color = CATEGORY_COLORS[cat] || "#999";
            return (
              <g key={cat}>
                <rect
                  x={minX}
                  y={minY}
                  width={maxX - minX}
                  height={maxY - minY}
                  rx={8}
                  fill={`${color}08`}
                  stroke={`${color}22`}
                  strokeWidth={1}
                />
                <text
                  x={minX + 10}
                  y={minY + 16}
                  fontSize="11px"
                  fill={color}
                  fontWeight="600"
                  opacity={0.8}
                >
                  {CATEGORY_LABELS[cat] || cat}
                </text>
              </g>
            );
          })}

          {links.map((l, i) => {
            const isActive =
              hoveredId && (l.s.id === hoveredId || l.t.id === hoveredId);
            const opacity = hoveredId ? (isActive ? 0.95 : 0.04) : 0.6;
            return (
              <line
                key={i}
                x1={l.s.x}
                y1={l.s.y}
                x2={l.t.x}
                y2={l.t.y}
                stroke="#E53935"
                strokeWidth={isActive ? 2.5 : 1.5}
                opacity={opacity}
                style={{ transition: "all 0.2s ease" }}
              />
            );
          })}

          {nodes.map((n) => {
            const color = CATEGORY_COLORS[n.cat || n.category] || "#999";
            const isConflict =
              hoveredId && hoveredExIds.has(n.id) && n.id !== hoveredId;
            const opacity = hoveredId ? (hoveredExIds.has(n.id) ? 1 : 0.15) : 1;
            return (
              <g
                key={n.id}
                onMouseEnter={() => setHoveredId(n.id)}
                onClick={() =>
                  setSelectedNode(selectedNode?.id === n.id ? null : n)
                }
                style={{ cursor: "pointer", transition: "opacity 0.2s ease" }}
                opacity={opacity}
              >
                <rect
                  x={n.x - NODE_W / 2}
                  y={n.y - NODE_H / 2}
                  width={NODE_W}
                  height={NODE_H}
                  rx={6}
                  fill={n.isSelected ? color : "#F5F5F5"}
                  stroke={
                    isConflict ? "#E53935" : n.isSelected ? color : "#DDD"
                  }
                  strokeWidth={isConflict ? 2.5 : n.isSelected ? 0 : 1}
                  strokeDasharray={isConflict ? "4,3" : "none"}
                  style={{ transition: "all 0.2s ease" }}
                />
                {n.isSelected && (
                  <text
                    x={n.x - NODE_W / 2 + 10}
                    y={n.y - 6}
                    fontSize="10px"
                    fill="rgba(255,255,255,0.7)"
                  >
                    ✓
                  </text>
                )}
                <text
                  x={n.x}
                  y={n.y - 5}
                  textAnchor="middle"
                  fontSize="10px"
                  fontWeight={n.isSelected ? "700" : "500"}
                  fill={n.isSelected ? "#fff" : "#333"}
                  style={{ pointerEvents: "none" }}
                >
                  {n.name.length > 9 ? n.name.slice(0, 9) + ".." : n.name}
                </text>
                {n.amount > 0 && (
                  <text
                    x={n.x}
                    y={n.y + 12}
                    textAnchor="middle"
                    fontSize="9px"
                    fill={n.isSelected ? "rgba(255,255,255,0.8)" : "#888"}
                    style={{ pointerEvents: "none" }}
                  >
                    {n.amount.toLocaleString()}만원
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {selectedNode && (
        <div
          className="graph-detail-overlay"
          onClick={() => setSelectedNode(null)}
        >
          <div
            className="graph-detail-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <button className="gdp-close" onClick={() => setSelectedNode(null)}>
              ✕
            </button>
            <div
              className="gdp-dot"
              style={{
                background:
                  CATEGORY_COLORS[selectedNode.cat || selectedNode.category] ||
                  "#D0D0D0",
              }}
            />
            <h3 className="gdp-title">{selectedNode.name}</h3>
            <div className="gdp-status">
              {selectedNode.isSelected ? (
                <span className="gdp-badge selected">✓ 최적 조합에 포함</span>
              ) : (
                <span className="gdp-badge excluded">
                  미선택 (배타 관계로 제외)
                </span>
              )}
            </div>
            <p className="gdp-provider">
              {selectedNode.host_org || selectedNode.provider}
            </p>
            {selectedNode.amount > 0 && (
              <div className="gdp-amount">
                {selectedNode.amount.toLocaleString()}만원
              </div>
            )}
            <p className="gdp-desc">
              {selectedNode.benefit_description || selectedNode.description}
            </p>

            {selectedNode.situational_condition && (
              <div className="gdp-period">
                <strong>신청 조건:</strong> {selectedNode.situational_condition}
              </div>
            )}
            {selectedNode.apply_start && (
              <div className="gdp-period">
                신청 기간: {selectedNode.apply_start} ~{" "}
                {selectedNode.apply_end || "미정"}
              </div>
            )}
            {(selectedNode.exclusive_with || []).length > 0 && (
              <div className="gdp-conflicts">
                <span className="gdp-conflicts-title">
                  ⚠️ 중복 수급 불가 정책
                </span>
                {selectedNode.exclusive_with.map((id) => {
                  const target = nodeMap[id];
                  return target ? (
                    <div
                      key={id}
                      className="gdp-conflict-item"
                      style={{ cursor: "pointer" }}
                      onClick={() => setSelectedNode(target)}
                    >
                      <span
                        className="gdp-conflict-dot"
                        style={{
                          background:
                            CATEGORY_COLORS[target.category] || "#D0D0D0",
                        }}
                      />
                      <span>{target.name}</span>
                      {selectedSubsidies?.[id] && (
                        <span className="gdp-conflict-selected">선택됨</span>
                      )}
                    </div>
                  ) : null;
                })}
              </div>
            )}
            {selectedNode.source_url && (
              <a
                href={selectedNode.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="gdp-apply-btn"
              >
                신청 페이지 →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ExclusionGraphPage;
