import { useMemo, useEffect, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import "./GraphPage.css";

const CATEGORY_COLORS = {
  employment: "#FB8C00",
  housing: "#43A047",
  finance: "#007AFF",
  health: "#00BCD4",
  culture: "#FF375F",
  military: "#5856D6",
  education: "#8E24AA",
};

function GraphPage({ selectedSubsidies }) {
  const [allPolicies, setAllPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const backendUrl = `http://${window.location.hostname}:8000`;
        const res = await fetch(`${backendUrl}/policies/?limit=100`);
        const data = await res.json();
        setAllPolicies(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("정책 로드 실패:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!allPolicies || allPolicies.length === 0)
      return { nodes: [], edges: [] };

    const total = allPolicies.length;
    const radius = Math.max(400, total * 32);

    const nodes = allPolicies.map((p, i) => {
      const angle = (2 * Math.PI * i) / total - Math.PI / 2;
      const x = radius + radius * Math.cos(angle);
      const y = radius + radius * Math.sin(angle);
      const isSelected = !!selectedSubsidies?.[p.id];
      const color = CATEGORY_COLORS[p.category] || "#999";

      return {
        id: p.id,
        position: { x, y },
        type: "default",
        data: { label: p.title },
        style: {
          background: isSelected ? color : "#fff",
          color: isSelected ? "#fff" : "#1a1a1a",
          border: `2px solid ${color}`,
          borderRadius: 8,
          padding: "6px 10px",
          fontSize: 11,
          fontWeight: isSelected ? 700 : 500,
          width: 150,
          textAlign: "center",
          boxShadow: isSelected
            ? `0 4px 16px ${color}55`
            : "0 1px 4px rgba(0,0,0,0.08)",
        },
      };
    });

    const addedEdges = new Set();
    const edges = [];
    allPolicies.forEach((p) => {
      if (!p.exclusive_with || p.exclusive_with.length === 0) return;
      p.exclusive_with.forEach((targetId) => {
        const edgeKey = [p.id, targetId].sort().join("|");
        if (addedEdges.has(edgeKey)) return;
        const target = allPolicies.find((x) => x.id === targetId);
        if (!target) return;
        addedEdges.add(edgeKey);

        const eitherSelected =
          selectedSubsidies?.[p.id] || selectedSubsidies?.[targetId];

        edges.push({
          id: edgeKey,
          source: p.id,
          target: targetId,
          style: {
            stroke: eitherSelected ? "#F44336" : "#d0d0d0",
            strokeWidth: eitherSelected ? 2 : 1,
            strokeDasharray: eitherSelected ? "none" : "5,5",
          },
          markerEnd: eitherSelected
            ? { type: MarkerType.ArrowClosed, color: "#F44336" }
            : undefined,
        });
      });
    });

    return { nodes, edges };
  }, [allPolicies, selectedSubsidies]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const selectedCount = allPolicies.filter(
    (p) => selectedSubsidies?.[p.id],
  ).length;
  const conflictCount = initialEdges.filter(
    (e) => selectedSubsidies?.[e.source] || selectedSubsidies?.[e.target],
  ).length;

  if (loading) {
    return (
      <div className="graph-page">
        <div className="graph-empty">
          <div className="graph-empty-icon">⏳</div>
          <h3>정책 데이터 불러오는 중...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div className="graph-header-left">
          <h2>정책 배타 관계 그래프</h2>
          <p className="graph-subtitle">
            동시에 수혜 불가한 정책 간의 관계를 시각화합니다
          </p>
        </div>
        <div className="graph-stats">
          <div className="graph-stat">
            <span className="graph-stat-value">{allPolicies.length}</span>
            <span className="graph-stat-label">전체 정책</span>
          </div>
          <div className="graph-stat accent">
            <span className="graph-stat-value">{selectedCount}</span>
            <span className="graph-stat-label">MWIS 선택</span>
          </div>
          <div className="graph-stat danger">
            <span className="graph-stat-value">{conflictCount}</span>
            <span className="graph-stat-label">배타 관계</span>
          </div>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-node-sample selected-sample" />
          <span>MWIS 선택 정책</span>
        </div>
        <div className="legend-item">
          <div className="legend-node-sample unselected-sample" />
          <span>미선택 정책</span>
        </div>
        <div className="legend-item">
          <div className="legend-edge-sample conflict-sample" />
          <span>배타 관계 (선택 포함)</span>
        </div>
        <div className="legend-item">
          <div className="legend-edge-sample normal-sample" />
          <span>배타 관계 (미선택)</span>
        </div>
      </div>

      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
          attributionPosition="bottom-right"
        >
          <Background color="#f0f0f0" gap={20} />
          <Controls />
          <MiniMap
            nodeColor={(n) =>
              n.style?.border?.replace("2px solid ", "") || "#999"
            }
            maskColor="rgba(255,255,255,0.8)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}

export default GraphPage;
