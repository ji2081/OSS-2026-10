import { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import "./ExclusionGraphPage.css";

const CATEGORY_COLORS = {
  housing: "#43A047",
  realestate: "#43A047",
  employment: "#FB8C00",
  education: "#FB8C00",
  finance: "#007AFF",
  asset: "#007AFF",
  culture: "#FF375F",
  health: "#00BCD4",
  welfare: "#5AC8FA",
  transport: "#8E24AA",
  startup: "#FB8C00",
  living: "#E53935",
  military: "#78909C",
};

function ExclusionGraphPage({ subsidies, selectedSubsidies, hasOptimized }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 600 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      setDimensions({ width: el.offsetWidth || 900, height: Math.max(el.offsetHeight, 550) });
    });
    obs.observe(el);
    setDimensions({ width: el.offsetWidth || 900, height: Math.max(el.offsetHeight, 550) });
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!subsidies || subsidies.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const { width, height } = dimensions;

    const nodes = subsidies.map((s) => ({
      id: s.id,
      name: s.name,
      category: s.category,
      amount: s.amount || 0,
      isSelected: !!selectedSubsidies?.[s.id],
      exclusive_with: s.exclusive_with || [],
      provider: s.provider,
      description: s.description,
      apply_start: s.apply_start,
      apply_end: s.apply_end,
      type: s.type,
      source_url: s.source_url,
    }));

    const nodeIds = new Set(nodes.map((n) => n.id));
    const links = [];
    const linkSet = new Set();
    nodes.forEach((node) => {
      (node.exclusive_with || []).forEach((targetId) => {
        if (nodeIds.has(targetId)) {
          const key = [node.id, targetId].sort().join("-");
          if (!linkSet.has(key)) {
            linkSet.add(key);
            links.push({ source: node.id, target: targetId });
          }
        }
      });
    });

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3.forceLink(links).id((d) => d.id).distance(200)
      )
      .force("charge", d3.forceManyBody().strength(-500))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => (d.isSelected ? 55 : 40)));

    const g = svg.append("g");

    const zoom = d3.zoom().scaleExtent([0.2, 3]).on("zoom", (event) => {
      g.attr("transform", event.transform);
    });
    svg.call(zoom);

    // 간선
    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#E53935")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "6,4")
      .attr("opacity", 0.3);

    // 간선 위 X 표시
    const linkLabels = g
      .append("g")
      .selectAll("text")
      .data(links)
      .enter()
      .append("text")
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#E53935")
      .attr("opacity", 0.4)
      .text("✕");

    // 노드 그룹
    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "graph-node")
      .attr("cursor", "pointer")
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // 노드 외곽 글로우 (선택된 것만)
    node
      .filter((d) => d.isSelected)
      .append("circle")
      .attr("r", 48)
      .attr("fill", "none")
      .attr("stroke", (d) => CATEGORY_COLORS[d.category] || "#666")
      .attr("stroke-width", 2)
      .attr("opacity", 0.2)
      .attr("class", "node-glow");

    // 노드 원형
    node
      .append("circle")
      .attr("r", (d) => (d.isSelected ? 40 : 28))
      .attr("fill", (d) =>
        d.isSelected ? CATEGORY_COLORS[d.category] || "#666" : "#888"
      )
      .attr("stroke", (d) => (d.isSelected ? "#fff" : "#aaa"))
      .attr("stroke-width", (d) => (d.isSelected ? 3 : 1.5))
      .attr("opacity", (d) => (d.isSelected ? 1 : 0.4))
      .attr("class", "node-circle");

    // 선택 체크 표시
    node
      .filter((d) => d.isSelected)
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-12px")
      .attr("font-size", "16px")
      .text("✓")
      .attr("fill", "#fff")
      .attr("class", "node-check");

    // 노드 이름
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", (d) => (d.isSelected ? "6px" : "4px"))
      .attr("font-size", (d) => (d.isSelected ? "11px" : "9px"))
      .attr("font-weight", (d) => (d.isSelected ? "600" : "400"))
      .attr("fill", (d) => (d.isSelected ? "#fff" : "#999"))
      .text((d) => (d.name.length > 7 ? d.name.slice(0, 7) + ".." : d.name))
      .attr("class", "node-label");

    // 금액 (선택된 것만)
    node
      .filter((d) => d.isSelected && d.amount > 0)
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "22px")
      .attr("font-size", "8px")
      .attr("fill", "#fff")
      .attr("opacity", 0.7)
      .text((d) => `${d.amount.toLocaleString()}만원`)
      .attr("class", "node-amount");

    // ── 호버 인터랙션 ──
    node
      .on("mouseover", function (event, d) {
        const exclusionIds = new Set(d.exclusive_with || []);
        exclusionIds.add(d.id);

        // 배타 관계 노드 → 빨간 테두리
        d3.selectAll(".node-circle")
          .transition().duration(200)
          .attr("opacity", (n) => {
            if (n.id === d.id) return 1;
            if (exclusionIds.has(n.id)) return 0.9;
            return 0.1;
          })
          .attr("stroke", (n) => {
            if (n.id === d.id) return "#fff";
            if (exclusionIds.has(n.id)) return "#E53935";
            return n.isSelected ? "#fff" : "#aaa";
          })
          .attr("stroke-width", (n) => {
            if (exclusionIds.has(n.id) && n.id !== d.id) return 4;
            return n.isSelected ? 3 : 1.5;
          });

        // 글로우도
        d3.selectAll(".node-glow")
          .transition().duration(200)
          .attr("opacity", (n) => exclusionIds.has(n.id) ? 0.3 : 0.05);

        // 라벨
        d3.selectAll(".node-label")
          .transition().duration(200)
          .attr("opacity", (n) => exclusionIds.has(n.id) ? 1 : 0.15);

        d3.selectAll(".node-check")
          .transition().duration(200)
          .attr("opacity", (n) => exclusionIds.has(n.id) ? 1 : 0.15);

        d3.selectAll(".node-amount")
          .transition().duration(200)
          .attr("opacity", (n) => exclusionIds.has(n.id) ? 0.8 : 0.05);

        // 간선 하이라이트
        link
          .transition().duration(200)
          .attr("opacity", (l) =>
            l.source.id === d.id || l.target.id === d.id ? 0.8 : 0.05
          )
          .attr("stroke-width", (l) =>
            l.source.id === d.id || l.target.id === d.id ? 3 : 1
          );

        linkLabels
          .transition().duration(200)
          .attr("opacity", (l) =>
            l.source.id === d.id || l.target.id === d.id ? 1 : 0.05
          )
          .attr("font-size", (l) =>
            l.source.id === d.id || l.target.id === d.id ? "16px" : "12px"
          );
      })
      .on("mouseout", function () {
        d3.selectAll(".node-circle")
          .transition().duration(300)
          .attr("opacity", (d) => (d.isSelected ? 1 : 0.4))
          .attr("stroke", (d) => (d.isSelected ? "#fff" : "#aaa"))
          .attr("stroke-width", (d) => (d.isSelected ? 3 : 1.5));

        d3.selectAll(".node-glow")
          .transition().duration(300)
          .attr("opacity", 0.2);

        d3.selectAll(".node-label")
          .transition().duration(300)
          .attr("opacity", 1);

        d3.selectAll(".node-check")
          .transition().duration(300)
          .attr("opacity", 1);

        d3.selectAll(".node-amount")
          .transition().duration(300)
          .attr("opacity", 0.7);

        link
          .transition().duration(300)
          .attr("opacity", 0.3)
          .attr("stroke-width", 1.5);

        linkLabels
          .transition().duration(300)
          .attr("opacity", 0.4)
          .attr("font-size", "12px");
      })
      .on("click", function (event, d) {
        setSelectedNode((prev) => (prev?.id === d.id ? null : d));
      });

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      linkLabels
        .attr("x", (d) => (d.source.x + d.target.x) / 2)
        .attr("y", (d) => (d.source.y + d.target.y) / 2);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [subsidies, selectedSubsidies, dimensions]);

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

  const totalExclusions = new Set();
  subsidies.forEach((s) =>
    (s.exclusive_with || []).forEach((id) => {
      const key = [s.id, id].sort().join("-");
      totalExclusions.add(key);
    })
  );

  return (
    <div className="graph-page">
      <div className="graph-header">
        <div>
          <h2>배타 관계 그래프</h2>
          <p className="graph-subtitle">
            정책 간 중복 수급 불가 관계를 시각화합니다. 노드를 드래그하거나 호버해보세요.
          </p>
        </div>
        <div className="graph-stats">
          <div className="gstat">
            <span className="gstat-num">{subsidies.length}</span>
            <span className="gstat-label">정책</span>
          </div>
          <div className="gstat">
            <span className="gstat-num">{totalExclusions.size}</span>
            <span className="gstat-label">배타 관계</span>
          </div>
          <div className="gstat">
            <span className="gstat-num">
              {subsidies.filter((s) => selectedSubsidies?.[s.id]).length}
            </span>
            <span className="gstat-label">선택됨</span>
          </div>
        </div>
      </div>

      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-circle selected" />
          <span>MWIS 선택 (컬러)</span>
        </div>
        <div className="legend-item">
          <span className="legend-circle unselected" />
          <span>미선택 (흑백)</span>
        </div>
        <div className="legend-item">
          <span className="legend-line" />
          <span>배타 관계 (중복 불가)</span>
        </div>
        <div className="legend-item">
          <span className="legend-hover-icon">◎</span>
          <span>호버 시 배타 정책 빨간 표시</span>
        </div>
      </div>

      <div className="graph-container" ref={containerRef}>
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="graph-svg"
        />
      </div>

      {/* 상세 패널 */}
      {selectedNode && (
        <div className="graph-detail-overlay" onClick={() => setSelectedNode(null)}>
          <div className="graph-detail-panel" onClick={(e) => e.stopPropagation()}>
            <button className="gdp-close" onClick={() => setSelectedNode(null)}>✕</button>
            <div
              className="gdp-dot"
              style={{
                background: selectedNode.isSelected
                  ? CATEGORY_COLORS[selectedNode.category] || "#666"
                  : "#888",
              }}
            />
            <h3 className="gdp-title">{selectedNode.name}</h3>
            <div className="gdp-status">
              {selectedNode.isSelected
                ? <span className="gdp-badge selected">✓ 최적 조합에 포함</span>
                : <span className="gdp-badge excluded">미선택</span>
              }
            </div>
            <p className="gdp-provider">{selectedNode.provider}</p>
            {selectedNode.amount > 0 && (
              <div className="gdp-amount">{selectedNode.amount.toLocaleString()}만원</div>
            )}
            <p className="gdp-desc">{selectedNode.description}</p>
            {selectedNode.apply_start && (
              <div className="gdp-period">
                신청 기간: {selectedNode.apply_start} ~ {selectedNode.apply_end || "미정"}
              </div>
            )}
            {selectedNode.exclusive_with.length > 0 && (
              <div className="gdp-conflicts">
                <span className="gdp-conflicts-title">⚠️ 중복 수급 불가 정책</span>
                {selectedNode.exclusive_with.map((id) => {
                  const target = subsidies.find((s) => s.id === id);
                  return target ? (
                    <div key={id} className="gdp-conflict-item">
                      <span
                        className="gdp-conflict-dot"
                        style={{
                          background: selectedSubsidies?.[id]
                            ? CATEGORY_COLORS[target.category] || "#666"
                            : "#888",
                        }}
                      />
                      <span>{target.name}</span>
                      {selectedSubsidies?.[id] && <span className="gdp-conflict-selected">선택됨</span>}
                    </div>
                  ) : null;
                })}
              </div>
            )}
            {selectedNode.source_url && (
              <a href={selectedNode.source_url} target="_blank" rel="noopener noreferrer" className="gdp-apply-btn">
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
