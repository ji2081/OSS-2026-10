import { useState } from "react";
import { supabase } from "../lib/supabaseClient";
import logoImg from "../logo.png";
import "./LoginPage.css";

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

  // 이메일 로그인
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("이메일과 비밀번호를 입력해주세요.");
      return;
    }
    setError("");
    const { data, error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (authError) {
      setError("로그인 실패: " + authError.message);
      return;
    }
    localStorage.setItem("access_token", data.session.access_token);
    onLogin(email.split("@")[0]);
  };

  // 소셜 로그인
  const handleSocialLogin = async (provider) => {
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: window.location.origin,
      },
    });
    if (authError) setError("소셜 로그인 실패: " + authError.message);
  };

  // 회원가입
  const handleSignup = async (e) => {
    e.preventDefault();
    if (!signupEmail.trim() || !signupPw.trim() || !signupPwConfirm.trim()) {
      setSignupError("모든 항목을 입력해주세요.");
      return;
    }
    if (signupPw !== signupPwConfirm) {
      setSignupError("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (signupPw.length < 6) {
      setSignupError("비밀번호는 6자 이상이어야 합니다.");
      return;
    }
    setSignupError("");
    const { error: authError } = await supabase.auth.signUp({
      email: signupEmail,
      password: signupPw,
    });
    if (authError) {
      setSignupError("가입 실패: " + authError.message);
      return;
    }
    setSignupSuccess(true);
    setTimeout(() => {
      setShowSignup(false);
      setSignupSuccess(false);
      setSignupEmail("");
      setSignupPw("");
      setSignupPwConfirm("");
      setEmail(signupEmail);
    }, 1500);
  };

  const closeSignup = () => {
    setShowSignup(false);
    setSignupError("");
    setSignupSuccess(false);
    setSignupEmail("");
    setSignupPw("");
    setSignupPwConfirm("");
  };

  return (
    <div className="login-container">
      <div className="login-bg-decoration">
        <div className="bg-circle bg-circle-1"></div>
        <div className="bg-circle bg-circle-2"></div>
        <div className="bg-circle bg-circle-3"></div>
      </div>
      <div className="login-card">
        <div className="login-header">
          <img
            src={logoImg}
            alt="다바짜"
            style={{ width: 48, height: 48, marginBottom: 16 }}
          />
          <h1 className="login-title">다바짜</h1>
          <p className="login-subtitle">청년지원금 최적조합탐색기</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="email">이메일</label>
            <input
              id="email"
              type="email"
              placeholder="이메일을 입력하세요"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">비밀번호</label>
            <input
              id="password"
              type="password"
              placeholder="비밀번호를 입력하세요"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button">
            로그인
          </button>
        </form>

        {/* 소셜 로그인 */}
        <div className="social-divider">
          <span>또는</span>
        </div>
        <div className="social-buttons">
          <button
            className="social-btn google"
            onClick={() => handleSocialLogin("google")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            Google
          </button>
          
          <button
            className="social-btn github"
            onClick={() => handleSocialLogin("github")}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path
                d="M12 1C5.37 1 0 6.37 0 13c0 5.3 3.44 9.8 8.2 11.39.6.11.82-.26.82-.58v-2.17c-3.34.73-4.04-1.42-4.04-1.42-.55-1.39-1.34-1.76-1.34-1.76-1.09-.74.08-.73.08-.73 1.2.09 1.84 1.24 1.84 1.24 1.07 1.84 2.81 1.31 3.5 1 .1-.78.42-1.31.76-1.61-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 016.02 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.82.58C20.56 22.8 24 18.3 24 13 24 6.37 18.63 1 12 1z"
                fill="#333"
              />
            </svg>
            GitHub
          </button>
        </div>

        <div className="login-footer">
          <p>
            계정이 없으신가요?{" "}
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                setShowSignup(true);
              }}
            >
              회원가입
            </a>
          </p>
        </div>
      </div>

      {/* 회원가입 모달 */}
      {showSignup && (
        <div className="modal-overlay" onClick={closeSignup}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeSignup}>
              ✕
            </button>
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
                  <input
                    id="signupEmail"
                    type="email"
                    placeholder="이메일을 입력하세요"
                    value={signupEmail}
                    onChange={(e) => setSignupEmail(e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="signupPw">비밀번호</label>
                  <input
                    id="signupPw"
                    type="password"
                    placeholder="비밀번호 (6자 이상)"
                    value={signupPw}
                    onChange={(e) => setSignupPw(e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="signupPwConfirm">비밀번호 확인</label>
                  <input
                    id="signupPwConfirm"
                    type="password"
                    placeholder="비밀번호를 다시 입력하세요"
                    value={signupPwConfirm}
                    onChange={(e) => setSignupPwConfirm(e.target.value)}
                  />
                </div>
                {signupError && <p className="login-error">{signupError}</p>}
                <button type="submit" className="login-button">
                  가입하기
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
export default LoginPage;
