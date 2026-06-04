import { useState, useRef, useEffect } from "react";
import { supabase } from "../lib/supabaseClient";
import * as d3 from "d3";
import logoImg from "../logo.png";
import "./LoginPage.css";

// 데모용 정책 데이터 (로그인 페이지 애니메이션용)
const DEMO_POLICIES = [
  { id: 1, name: "청년수당", category: "living", selected: true },
  { id: 2, name: "월세지원(국토부)", category: "housing", selected: true },
  { id: 3, name: "월세지원(서울시)", category: "housing", selected: false },
  { id: 4, name: "내일채움공제", category: "employment", selected: true },
  { id: 5, name: "국민취업지원", category: "employment", selected: false },
  { id: 6, name: "희망두배적금", category: "finance", selected: true },
  { id: 7, name: "청년내일저축", category: "finance", selected: false },
  { id: 8, name: "K-패스", category: "transport", selected: true },
  { id: 9, name: "교통비지원", category: "transport", selected: false },
  { id: 10, name: "문화누리카드", category: "culture", selected: true },
  { id: 11, name: "마음건강바우처", category: "health", selected: true },
  { id: 12, name: "도약계좌", category: "finance", selected: false },
  { id: 13, name: "전세자금대출", category: "housing", selected: false },
  { id: 14, name: "취업성공패키지", category: "employment", selected: false },
  { id: 15, name: "청년문화패스", category: "culture", selected: false },
  { id: 16, name: "생활용품지원", category: "welfare", selected: false },
  { id: 17, name: "건강검진지원", category: "health", selected: false },
  { id: 18, name: "시험응시료", category: "employment", selected: true },
];

const DEMO_EXCLUSIONS = [
  [2, 3], [4, 5], [6, 7], [6, 12], [7, 12], [8, 9], [1, 14], [10, 15], [11, 17],
];

const COLORS = {
  living: "#E53935", housing: "#43A047", employment: "#FB8C00",
  finance: "#007AFF", transport: "#8E24AA", culture: "#FF375F",
  health: "#00BCD4", welfare: "#5AC8FA",
};

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [showSignup, setShowSignup] = useState(false);
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPw, setSignupPw] = useState("");
  const [signupPwConfirm, setSignupPwConfirm] = useState("");
  const [signupError, setSignupError] = useState("");
  const [signupSuccess, setSignupSuccess] = useState(false);

  const [phase, setPhase] = useState(0); // 0: graph full, 1: edges, 2: fade, 3: slide
  const [showLogin, setShowLogin] = useState(false);
  const svgRef = useRef(null);
  const simRef = useRef(null);

  // 애니메이션 타이밍
  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 1200),   // 간선 표시
      setTimeout(() => setPhase(2), 2500),   // 비선택 페이드아웃
      setTimeout(() => setPhase(3), 4000),   // 오른쪽으로 밀림
      setTimeout(() => setShowLogin(true), 4800), // 로그인 폼 등장
    ];
    return () => timers.forEach(clearTimeout);
  }, []);

  // D3 그래프
  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = window.innerWidth;
    const height = window.innerHeight;

    const nodes = DEMO_POLICIES.map((p) => ({
      ...p,
      x: width / 2 + (Math.random() - 0.5) * width * 0.6,
      y: height / 2 + (Math.random() - 0.5) * height * 0.6,
    }));

    const links = DEMO_EXCLUSIONS.map(([s, t]) => ({
      source: nodes.find((n) => n.id === s),
      target: nodes.find((n) => n.id === t),
    }));

    const simulation = d3
      .forceSimulation(nodes)
      .force("link", d3.forceLink(links).distance(140).strength(0.3))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(55));

    simRef.current = simulation;

    const g = svg.append("g").attr("class", "graph-group");

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
      .attr("opacity", 0)
      .attr("class", "demo-link");

    // 노드 그룹
    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "demo-node")
      .attr("opacity", 0);

    // 노드 원형
    node
      .append("circle")
      .attr("r", 38)
      .attr("fill", (d) => COLORS[d.category] || "#666")
      .attr("opacity", 0.85)
      .attr("stroke", "rgba(255,255,255,0.3)")
      .attr("stroke-width", 2);

    // 노드 라벨
    node
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "4px")
      .attr("font-size", "11px")
      .attr("font-weight", "500")
      .attr("fill", "#fff")
      .text((d) => (d.name.length > 5 ? d.name.slice(0, 5) + ".." : d.name));

    // 노드 순차 등장
    node.each(function (d, i) {
      d3.select(this)
        .transition()
        .delay(i * 60)
        .duration(400)
        .attr("opacity", 1);
    });

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);
      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, []);

  // Phase 1: 간선 등장
  useEffect(() => {
    if (phase >= 1) {
      d3.selectAll(".demo-link")
        .transition()
        .duration(800)
        .attr("opacity", 0.5);
    }
  }, [phase]);

  // Phase 2: 비선택 노드 페이드아웃
  useEffect(() => {
    if (phase >= 2) {
      d3.selectAll(".demo-node")
        .filter((d) => !d.selected)
        .transition()
        .duration(500)
        .attr("opacity", 0.08);

      d3.selectAll(".demo-node")
        .filter((d) => d.selected)
        .select("circle")
        .transition()
        .duration(800)
        .attr("r", 44)
        .attr("stroke", "rgba(255,255,255,0.6)")
        .attr("stroke-width", 3);

      d3.selectAll(".demo-link")
        .transition()
        .delay(400)
        .duration(800)
        .attr("opacity", 0.15);
    }
  }, [phase]);

  // Phase 3: 그래프 오른쪽으로 슬라이드
  useEffect(() => {
    if (phase >= 3) {
      d3.select(".graph-group")
        .transition()
        .duration(1200)
        .ease(d3.easeCubicInOut)
        .attr("transform", `translate(${window.innerWidth * 0.2}, 0) scale(0.75)`);
    }
  }, [phase]);

  // 로그인
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("이메일과 비밀번호를 입력해주세요.");
      return;
    }
    setError("");
    const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });
    if (authError) { setError("로그인 실패: " + authError.message); return; }
    localStorage.setItem("access_token", data.session.access_token);
    onLogin(email.split("@")[0]);
  };

  const handleSocialLogin = async (provider) => {
    const { error: authError } = await supabase.auth.signInWithOAuth({ provider });
    if (authError) setError("소셜 로그인 실패: " + authError.message);
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    if (!signupEmail.trim() || !signupPw.trim() || !signupPwConfirm.trim()) {
      setSignupError("모든 항목을 입력해주세요."); return;
    }
    if (signupPw !== signupPwConfirm) { setSignupError("비밀번호가 일치하지 않습니다."); return; }
    if (signupPw.length < 6) { setSignupError("비밀번호는 6자 이상이어야 합니다."); return; }
    setSignupError("");
    const { error: authError } = await supabase.auth.signUp({ email: signupEmail, password: signupPw });
    if (authError) { setSignupError("가입 실패: " + authError.message); return; }
    setSignupSuccess(true);
    setTimeout(() => {
      setShowSignup(false); setSignupSuccess(false);
      setSignupEmail(""); setSignupPw(""); setSignupPwConfirm("");
      setEmail(signupEmail);
    }, 2000);
  };

  const closeSignup = () => {
    setShowSignup(false); setSignupError(""); setSignupSuccess(false);
    setSignupEmail(""); setSignupPw(""); setSignupPwConfirm("");
  };

  return (
    <div className="login-container-v2">
      {/* 배경 그래프 */}
      <svg ref={svgRef} className="bg-graph" />

      {/* 로그인 폼 */}
      <div className={`login-panel ${showLogin ? "visible" : ""}`}>
        <div className="login-card-v2">
          <div className="login-header">
            <img src={logoImg} alt="다바짜" className="login-logo" />
            <h1 className="login-title">다바짜</h1>
            <p className="login-subtitle">청년지원금 최적조합탐색기</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="input-group">
              <label htmlFor="email">이메일</label>
              <input id="email" type="email" placeholder="이메일을 입력하세요" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="input-group">
              <label htmlFor="password">비밀번호</label>
              <input id="password" type="password" placeholder="비밀번호를 입력하세요" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <p className="login-error">{error}</p>}
            <button type="submit" className="login-button">로그인</button>
          </form>

          <div className="social-divider"><span>또는</span></div>
          <div className="social-buttons">
            <button className="social-btn google" onClick={() => handleSocialLogin('google')}>
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Google
            </button>
            <button className="social-btn github" onClick={() => handleSocialLogin('github')}>
              <svg width="18" height="18" viewBox="0 0 24 24"><path d="M12 1C5.37 1 0 6.37 0 13c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58v-2.17c-3.34.73-4.04-1.42-4.04-1.42-.55-1.39-1.34-1.76-1.34-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .1-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 016.02 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.82.58C20.56 22.8 24 18.3 24 13 24 6.37 18.63 1 12 1z" fill="#333"/></svg>
              GitHub
            </button>
          </div>

          <div className="login-footer">
            <p>계정이 없으신가요? <a href="#" onClick={(e) => { e.preventDefault(); setShowSignup(true); }}>회원가입</a></p>
          </div>
        </div>
      </div>

      {/* 회원가입 모달 */}
      {showSignup && (
        <div className="modal-overlay" onClick={closeSignup}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeSignup}>✕</button>
            <div className="login-header">
              <h1 className="login-title">회원가입</h1>
              <p className="login-subtitle">이메일로 가입하세요</p>
            </div>
            {signupSuccess ? (
              <div className="signup-success">
                <div className="success-icon">✅</div>
                <p>회원가입이 완료되었습니다!</p>
                <span>입력하신 이메일로 인증 메일이 발송되었습니다.</span>
                <span style={{ display: 'block', marginTop: 8, fontSize: 12, color: '#999' }}>
                  메일함에서 "Confirm your mail"을 클릭한 후 로그인해주세요.
                </span>
              </div>
            ) : (
              <form onSubmit={handleSignup} className="login-form">
                <div className="input-group">
                  <label htmlFor="signupEmail">이메일</label>
                  <input id="signupEmail" type="email" placeholder="이메일을 입력하세요" value={signupEmail} onChange={(e) => setSignupEmail(e.target.value)} />
                </div>
                <div className="input-group">
                  <label htmlFor="signupPw">비밀번호</label>
                  <input id="signupPw" type="password" placeholder="비밀번호 (6자 이상)" value={signupPw} onChange={(e) => setSignupPw(e.target.value)} />
                </div>
                <div className="input-group">
                  <label htmlFor="signupPwConfirm">비밀번호 확인</label>
                  <input id="signupPwConfirm" type="password" placeholder="비밀번호를 다시 입력하세요" value={signupPwConfirm} onChange={(e) => setSignupPwConfirm(e.target.value)} />
                </div>
                {signupError && <p className="login-error">{signupError}</p>}
                <button type="submit" className="login-button">가입하기</button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default LoginPage;
