import { useState, useMemo, useEffect, useCallback } from "react";
import ReactFlow, {
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  StraightEdge,
  useViewport,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
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
  rights: "#FF6B35",
  scholarship: "#E91E63",
};

const CATEGORY_LABELS = {
  employment: "취업·교육",
  housing: "주거",
  finance: "금융·자산",
  health: "건강·복지",
  culture: "문화",
  military: "군장병",
  education: "교육",
  scholarship: "장학금",
  welfare: "복지",
  rights: "권리·법률",
  startup: "창업",
};

const NODE_W = 130;
const NODE_H = 52;
const COL_GAP = 24;
const ROW_GAP = 18;
const SECTION_GAP = 40;
const PADDING = 32;

function buildLayout(
  allPolicies,
  selectedSubsidies,
  hoveredId,
  hoveredExIds,
  onHover,
) {
  const byCategory = {};
  allPolicies.forEach((s) => {
    const cat = s.category || "etc";
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(s);
  });

  const catKeys = Object.keys(byCategory);
  const rfNodes = [];
  const posMap = {};
  const categoryBounds = {};
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

    const catStartX = x - 10;
    const catStartY = y - 10;

    items.forEach((s, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const px = x + col * (NODE_W + COL_GAP);
      const py = y + 28 + row * (NODE_H + ROW_GAP);
      posMap[s.id] = { x: px, y: py };
      rfNodes.push({
        id: s.id,
        type: "policyNode",
        position: { x: px, y: py },
        data: {
          label: s.title || s.name,
          amount:
            s.tiers && s.tiers.length > 0
              ? Math.round(
                  (s.tiers[0].monthly_benefit * s.tiers[0].duration_months) /
                    10000,
                )
              : s.amount || 0,
          isSelected: !!selectedSubsidies?.[s.id],
          cat,
          policy: s,
          hoveredId,
          hoveredExIds,
          onHover,
        },
      });
    });

    const catW = cols * (NODE_W + COL_GAP) - COL_GAP + 20;
    const catH = sHeight + 28 + 20;
    categoryBounds[cat] = { x: catStartX, y: catStartY, w: catW, h: catH };

    if (idx % 2 === 0) {
      x += sectionWidth;
    } else {
      x = PADDING;
    }
    rowMaxH = Math.max(rowMaxH, sHeight + 28);
  });

  return { rfNodes, byCategory, posMap, categoryBounds };
}

function PolicyNode({ data, id }) {
  const color = CATEGORY_COLORS[data.cat] || "#999";
  const isConflict =
    data.hoveredId && data.hoveredExIds?.has(id) && id !== data.hoveredId;
  const opacity = data.hoveredId ? (data.hoveredExIds?.has(id) ? 1 : 0.15) : 1;
  return (
    <div
      onMouseEnter={() => data.onHover(id)}
      onMouseLeave={() => data.onHover(null)}
      style={{
        width: NODE_W,
        height: NODE_H,
        borderRadius: 6,
        background: data.isSelected ? color : "#F5F5F5",
        border: isConflict
          ? `2.5px dashed #E53935`
          : `1px solid ${data.isSelected ? color : "#DDD"}`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "all 0.2s ease",
        padding: "4px 8px",
        boxSizing: "border-box",
        opacity,
      }}
    >
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      {data.isSelected && (
        <span
          style={{
            position: "absolute",
            top: 4,
            left: 8,
            fontSize: 10,
            color: "rgba(255,255,255,0.7)",
          }}
        >
          ✓
        </span>
      )}
      <span
        style={{
          fontSize: 10,
          fontWeight: data.isSelected ? 700 : 500,
          color: data.isSelected ? "#fff" : "#333",
          textAlign: "center",
          lineHeight: 1.3,
        }}
      >
        {data.label.length > 9 ? data.label.slice(0, 9) + ".." : data.label}
      </span>
      {data.amount > 0 && (
        <span
          style={{
            fontSize: 9,
            color: data.isSelected ? "rgba(255,255,255,0.8)" : "#888",
            marginTop: 2,
          }}
        >
          {data.amount.toLocaleString()}만원
        </span>
      )}
    </div>
  );
}

const nodeTypes = { policyNode: PolicyNode };
const edgeTypes = { default: StraightEdge };

function CategoryBackground({ categoryBounds }) {
  const { x, y, zoom } = useViewport();
  return (
    <svg
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: 0,
      }}
    >
      <g transform={`translate(${x},${y}) scale(${zoom})`}>
        {Object.entries(categoryBounds).map(([cat, b]) => {
          const color = CATEGORY_COLORS[cat] || "#999";
          return (
            <g key={cat}>
              <rect
                x={b.x}
                y={b.y}
                width={b.w}
                height={b.h}
                rx={8}
                fill={`${color}08`}
                stroke={`${color}22`}
                strokeWidth={1}
              />
              <text
                x={b.x + 10}
                y={b.y + 16}
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
      </g>
    </svg>
  );
}

function ExclusionGraphPage({ selectedSubsidies, hasOptimized }) {
  const [allPolicies, setAllPolicies] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredId, setHoveredId] = useState(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [categoryBounds, setCategoryBounds] = useState({});

  useEffect(() => {
    const handler = (e) => {
      if (e.message?.includes("ResizeObserver")) e.stopImmediatePropagation();
    };
    window.addEventListener("error", handler);
    return () => window.removeEventListener("error", handler);
  }, []);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const backendUrl = process.env.REACT_APP_API_URL || "https://oss-2026-10-production.up.railway.app";
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

  const nodeMap = useMemo(() => {
    const m = {};
    allPolicies.forEach((p) => (m[p.id] = p));
    return m;
  }, [allPolicies]);

  const hoveredExIds = useMemo(() => {
    const s = new Set();
    if (!hoveredId) return s;
    s.add(hoveredId);
    const n = nodeMap[hoveredId];
    if (n) (n.exclusive_with || []).forEach((id) => s.add(id));
    return s;
  }, [hoveredId, nodeMap]);

  useEffect(() => {
    if (allPolicies.length === 0) return;
    const { rfNodes, categoryBounds: cb } = buildLayout(
      allPolicies,
      selectedSubsidies || {},
      hoveredId,
      hoveredExIds,
      setHoveredId,
    );
    setNodes(rfNodes);
    setCategoryBounds(cb);

    const seen = new Set();
    const rfEdges = [];
    allPolicies.forEach((p) => {
      (p.exclusive_with || []).forEach((tid) => {
        const key = [p.id, tid].sort().join("|");
        if (!seen.has(key) && allPolicies.find((x) => x.id === tid)) {
          seen.add(key);
          rfEdges.push({
            id: key,
            source: p.id,
            target: tid,
            type: "straight",
            style: {
              stroke: "#E53935",
              strokeWidth:
                hoveredId && (p.id === hoveredId || tid === hoveredId)
                  ? 2.5
                  : 1.5,
              opacity: hoveredId
                ? p.id === hoveredId || tid === hoveredId
                  ? 0.95
                  : 0.04
                : 0.6,
            },
          });
        }
      });
    });
    setEdges(rfEdges);
  }, [allPolicies, selectedSubsidies, hoveredId, hoveredExIds]);

  const onNodeClick = useCallback(
    (_, node) => {
      const policy = allPolicies.find((p) => p.id === node.id);
      setSelectedNode((prev) => (prev?.id === node.id ? null : policy));
    },
    [allPolicies],
  );

  const totalExclusions = useMemo(() => edges.length, [edges]);

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
            <span className="gstat-num">{totalExclusions}</span>
            <span className="gstat-label">배타 관계</span>
          </div>
          <div className="gstat">
            <span className="gstat-num">
              {nodes.filter((n) => n.data?.isSelected).length}
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

      <div
        className="graph-container eg-scroll"
        style={{ height: 600, position: "relative" }}
      >
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
            style={{ background: "transparent" }}
            defaultEdgeOptions={{ type: "straight" }}
          >
            <CategoryBackground categoryBounds={categoryBounds} />
          </ReactFlow>
        </ReactFlowProvider>
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
                background: CATEGORY_COLORS[selectedNode.category] || "#D0D0D0",
              }}
            />
            <h3 className="gdp-title">
              {selectedNode.title || selectedNode.name}
            </h3>
            <div className="gdp-status">
              {selectedSubsidies?.[selectedNode.id] ? (
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
                      <span>{target.title || target.name}</span>
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
