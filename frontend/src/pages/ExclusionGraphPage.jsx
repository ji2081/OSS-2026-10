import { useRef, useEffect, useState } from "react";
import "./ExclusionGraphPage.css";

const CATEGORY_COLORS = {
  housing: "#43A047", realestate: "#43A047", employment: "#FB8C00",
  education: "#FB8C00", finance: "#007AFF", asset: "#007AFF",
  culture: "#FF375F", health: "#00BCD4", welfare: "#5AC8FA",
  transport: "#8E24AA", startup: "#FB8C00", living: "#E53935", military: "#78909C",
};

function ExclusionGraphPage({ subsidies, selectedSubsidies, hasOptimized }) {
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredId, setHoveredId] = useState(null);
  const [dims, setDims] = useState({ w: 1000, h: 650 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => setDims({ w: el.offsetWidth || 1000, h: 650 }));
    obs.observe(el);
    setDims({ w: el.offsetWidth || 1000, h: 650 });
    return () => obs.disconnect();
  }, []);

  if (!hasOptimized || !subsidies || subsidies.length === 0) {
    return (
      <div className="graph-page">
        <div className="graph-empty">
          <div className="graph-empty-icon">🕸️</div>
          <h3>먼저 최적 조합을 탐색해주세요</h3>
          <p>대시보드에서 조건을 설정하고 "최적 조합 탐색"을 눌러주세요.</p>
        </div>
      </div>
    );
  }

  const { w, h } = dims;
  const cx = w / 2;
  const cy = h / 2;

  // 선택된 것 / 미선택 분리
  const selectedList = subsidies.filter((s) => selectedSubsidies?.[s.id]);
  const unselectedList = subsidies.filter((s) => !selectedSubsidies?.[s.id]);

  // 선택된 노드: 안쪽 원 (중앙 가까이)
  const innerRadius = Math.min(w, h) * 0.2;
  const selectedNodes = selectedList.map((s, i) => {
    const angle = (2 * Math.PI * i) / selectedList.length - Math.PI / 2;
    return {
      ...s, isSelected: true,
      x: cx + innerRadius * Math.cos(angle),
      y: cy + innerRadius * Math.sin(angle),
      r: 38,
    };
  });

  // 미선택 노드: 바깥쪽 원
  const outerRadius = Math.min(w, h) * 0.42;
  const unselectedNodes = unselectedList.map((s, i) => {
    const angle = (2 * Math.PI * i) / unselectedList.length - Math.PI / 2;
    return {
      ...s, isSelected: false,
      x: cx + outerRadius * Math.cos(angle),
      y: cy + outerRadius * Math.sin(angle),
      r: 20,
    };
  });

  const nodes = [...selectedNodes, ...unselectedNodes];
  const nodeMap = {};
  nodes.forEach((n) => { nodeMap[n.id] = n; });

  // 간선
  const links = [];
  const linkSet = new Set();
  nodes.forEach((n) => {
    (n.exclusive_with || []).forEach((tid) => {
      if (nodeMap[tid]) {
        const key = [n.id, tid].sort().join("-");
        if (!linkSet.has(key)) { linkSet.add(key); links.push({ s: n, t: nodeMap[tid] }); }
      }
    });
  });

  // 호버 관련
  const hoveredExIds = new Set();
  if (hoveredId) {
    hoveredExIds.add(hoveredId);
    const hNode = nodeMap[hoveredId];
    if (hNode) (hNode.exclusive_with || []).forEach((id) => hoveredExIds.add(id));
  }

  const getNodeOpacity = (n) => {
    if (!hoveredId) return n.isSelected ? 1 : 0.5;
    if (n.id === hoveredId) return 1;
    if (hoveredExIds.has(n.id)) return 0.9;
    return 0.06;
  };

  const getLabelOpacity = (n) => {
    if (!hoveredId) return n.isSelected ? 1 : 0.7;
    if (hoveredExIds.has(n.id)) return 1;
    return 0.06;
  };

  const getLinkOpacity = (l) => {
    if (!hoveredId) return 0.2;
    if (l.s.id === hoveredId || l.t.id === hoveredId) return 0.8;
    return 0.03;
  };

  const getLinkWidth = (l) => {
    if (!hoveredId) return 1.5;
    if (l.s.id === hoveredId || l.t.id === hoveredId) return 2.5;
    return 1;
  };

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div>
          <h2>배타 관계 그래프</h2>
          <p className="graph-subtitle">안쪽 = 최적 선택 정책, 바깥쪽 = 미선택 정책. 노드를 호버해보세요.</p>
        </div>
        <div className="graph-stats">
          <div className="gstat"><span className="gstat-num">{subsidies.length}</span><span className="gstat-label">정책</span></div>
          <div className="gstat"><span className="gstat-num">{linkSet.size}</span><span className="gstat-label">배타 관계</span></div>
          <div className="gstat"><span className="gstat-num">{selectedList.length}</span><span className="gstat-label">선택됨</span></div>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item"><span className="legend-circle selected" /><span>최적 선택 (안쪽)</span></div>
        <div className="legend-item"><span className="legend-circle unselected" /><span>미선택 (바깥쪽)</span></div>
        <div className="legend-item"><span className="legend-line" /><span>중복 수급 불가</span></div>
      </div>

      <div className="graph-container" ref={containerRef}>
        <svg width={w} height={h} className="graph-svg" onMouseLeave={() => setHoveredId(null)}>

          {/* 간선 */}
          {links.map((l, i) => {
            const midX = (l.s.x + l.t.x) / 2;
            const midY = (l.s.y + l.t.y) / 2;
            const isActive = hoveredId && (l.s.id === hoveredId || l.t.id === hoveredId);
            return (
              <g key={`link-${i}`}>
                <line
                  x1={l.s.x} y1={l.s.y} x2={l.t.x} y2={l.t.y}
                  stroke="#E53935" strokeWidth={getLinkWidth(l)}
                  strokeDasharray="8,5" opacity={getLinkOpacity(l)}
                  style={{ transition: "all 0.25s ease" }}
                />
                <text x={midX} y={midY} textAnchor="middle" dominantBaseline="central"
                  fontSize={isActive ? "14px" : "10px"} fill="#E53935"
                  opacity={getLinkOpacity(l)} fontWeight="bold"
                  style={{ transition: "all 0.25s ease" }}
                >✕</text>
              </g>
            );
          })}

          {/* 미선택 노드 (뒤에 렌더) */}
          {unselectedNodes.map((n) => (
            <g key={n.id} onMouseEnter={() => setHoveredId(n.id)}
              onClick={() => setSelectedNode(selectedNode?.id === n.id ? null : n)}
              style={{ cursor: "pointer" }}>
              <circle cx={n.x} cy={n.y} r={n.r}
                fill="#D0D0D0" stroke="none"
                opacity={getNodeOpacity(n)}
                style={{ transition: "all 0.25s ease" }}
              />
              {/* 호버시 배타 대상이면 빨간 점선 테두리 */}
              {hoveredId && hoveredExIds.has(n.id) && n.id !== hoveredId && (
                <circle cx={n.x} cy={n.y} r={n.r + 4}
                  fill="none" stroke="#E53935" strokeWidth={2.5}
                  strokeDasharray="4,3" opacity={0.9}
                />
              )}
              <text x={n.x} y={n.y + 3} textAnchor="middle" fontSize="8px"
                fill="#555" fontWeight="400" opacity={getLabelOpacity(n)}
                style={{ transition: "opacity 0.25s ease", pointerEvents: "none" }}
              >{n.name.length > 6 ? n.name.slice(0, 6) + ".." : n.name}</text>
            </g>
          ))}

          {/* 선택된 노드 (앞에 렌더) */}
          {selectedNodes.map((n) => (
            <g key={n.id} onMouseEnter={() => setHoveredId(n.id)}
              onClick={() => setSelectedNode(selectedNode?.id === n.id ? null : n)}
              style={{ cursor: "pointer" }}>
              {/* 글로우 */}
              <circle cx={n.x} cy={n.y} r={n.r + 10}
                fill="none" stroke={CATEGORY_COLORS[n.category] || "#666"}
                strokeWidth={2} opacity={hoveredId ? (hoveredExIds.has(n.id) ? 0.4 : 0.08) : 0.25}
                style={{ transition: "all 0.25s ease" }}
              />
              {/* 메인 원 */}
              <circle cx={n.x} cy={n.y} r={n.r}
                fill={CATEGORY_COLORS[n.category] || "#666"}
                stroke="#fff" strokeWidth={3}
                opacity={getNodeOpacity(n)}
                style={{ transition: "all 0.25s ease" }}
              />
              {/* 체크 */}
              <text x={n.x} y={n.y - 12} textAnchor="middle" fontSize="14px" fill="#fff"
                opacity={getLabelOpacity(n)}
                style={{ transition: "opacity 0.25s ease", pointerEvents: "none" }}
              >✓</text>
              {/* 이름 */}
              <text x={n.x} y={n.y + 5} textAnchor="middle" fontSize="10px"
                fill="#fff" fontWeight="600" opacity={getLabelOpacity(n)}
                style={{ transition: "opacity 0.25s ease", pointerEvents: "none" }}
              >{n.name.length > 7 ? n.name.slice(0, 7) + ".." : n.name}</text>
              {/* 금액 */}
              {n.amount > 0 && (
                <text x={n.x} y={n.y + 20} textAnchor="middle" fontSize="8px"
                  fill="#fff" opacity={hoveredId ? (hoveredExIds.has(n.id) ? 0.8 : 0.05) : 0.7}
                  style={{ transition: "opacity 0.25s ease", pointerEvents: "none" }}
                >{n.amount.toLocaleString()}만원</text>
              )}
            </g>
          ))}
        </svg>
      </div>

      {/* 상세 패널 */}
      {selectedNode && (
        <div className="graph-detail-overlay" onClick={() => setSelectedNode(null)}>
          <div className="graph-detail-panel" onClick={(e) => e.stopPropagation()}>
            <button className="gdp-close" onClick={() => setSelectedNode(null)}>✕</button>
            <div className="gdp-dot" style={{ background: selectedNode.isSelected ? CATEGORY_COLORS[selectedNode.category] || "#666" : "#D0D0D0" }} />
            <h3 className="gdp-title">{selectedNode.name}</h3>
            <div className="gdp-status">
              {selectedNode.isSelected ? <span className="gdp-badge selected">✓ 최적 조합에 포함</span> : <span className="gdp-badge excluded">미선택 (배타 관계로 제외)</span>}
            </div>
            <p className="gdp-provider">{selectedNode.provider}</p>
            {selectedNode.amount > 0 && <div className="gdp-amount">{selectedNode.amount.toLocaleString()}만원</div>}
            <p className="gdp-desc">{selectedNode.description}</p>
            {selectedNode.apply_start && <div className="gdp-period">신청 기간: {selectedNode.apply_start} ~ {selectedNode.apply_end || "미정"}</div>}
            {(selectedNode.exclusive_with || []).length > 0 && (
              <div className="gdp-conflicts">
                <span className="gdp-conflicts-title">⚠️ 중복 수급 불가 정책</span>
                {selectedNode.exclusive_with.map((id) => {
                  const target = subsidies.find((s) => s.id === id);
                  return target ? (
                    <div key={id} className="gdp-conflict-item">
                      <span className="gdp-conflict-dot" style={{ background: selectedSubsidies?.[id] ? CATEGORY_COLORS[target.category] || "#666" : "#D0D0D0" }} />
                      <span>{target.name}</span>
                      {selectedSubsidies?.[id] && <span className="gdp-conflict-selected">선택됨</span>}
                    </div>
                  ) : null;
                })}
              </div>
            )}
            {selectedNode.source_url && (
              <a href={selectedNode.source_url} target="_blank" rel="noopener noreferrer" className="gdp-apply-btn">신청 페이지 →</a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ExclusionGraphPage;
