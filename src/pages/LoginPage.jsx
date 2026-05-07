import { useState } from 'react'
import logoImg from '../logo.png'
import './LoginPage.css'

function LoginPage({ onLogin }) {
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [showSignup, setShowSignup] = useState(false)
  const [signupId, setSignupId] = useState('')
  const [signupPw, setSignupPw] = useState('')
  const [signupPwConfirm, setSignupPwConfirm] = useState('')
  const [signupError, setSignupError] = useState('')
  const [signupSuccess, setSignupSuccess] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!userId.trim() || !password.trim()) { setError('아이디와 비밀번호를 입력해주세요.'); return }
    setError('')
    onLogin(userId)
  }
  const handleSignup = (e) => {
    e.preventDefault()
    if (!signupId.trim() || !signupPw.trim() || !signupPwConfirm.trim()) { setSignupError('모든 항목을 입력해주세요.'); return }
    if (signupPw !== signupPwConfirm) { setSignupError('비밀번호가 일치하지 않습니다.'); return }
    if (signupPw.length < 4) { setSignupError('비밀번호는 4자 이상이어야 합니다.'); return }
    setSignupError('')
    setSignupSuccess(true)
    setTimeout(() => { setShowSignup(false); setSignupSuccess(false); setSignupId(''); setSignupPw(''); setSignupPwConfirm(''); setUserId(signupId); }, 1500)
  }
  const closeSignup = () => { setShowSignup(false); setSignupError(''); setSignupSuccess(false); setSignupId(''); setSignupPw(''); setSignupPwConfirm(''); }

  return (
    <div className="login-container">
      <div className="login-bg-decoration">
        <div className="bg-circle bg-circle-1"></div>
        <div className="bg-circle bg-circle-2"></div>
        <div className="bg-circle bg-circle-3"></div>
      </div>
      <div className="login-card">
       <div className="login-header">
         <img src={logoImg} alt="다바짜" style={{ width: 48, height: 48, marginBottom: 16 }} />
          <h1 className="login-title">다바짜</h1>
          <p className="login-subtitle">청년지원금 최적조합탐색기</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label htmlFor="userId">아이디</label>
            <input id="userId" type="text" placeholder="아이디를 입력하세요" value={userId} onChange={(e) => setUserId(e.target.value)} />
          </div>
          <div className="input-group">
            <label htmlFor="password">비밀번호</label>
            <input id="password" type="password" placeholder="비밀번호를 입력하세요" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button">로그인</button>
        </form>
        <div className="login-footer">
          <p>계정이 없으신가요? <a href="#" onClick={(e) => { e.preventDefault(); setShowSignup(true) }}>회원가입</a></p>
        </div>
        <div className="login-dev-notice"><p>🔧 개발 모드: 아무 값이나 입력하면 로그인됩니다</p></div>
      </div>
      {showSignup && (
        <div className="modal-overlay" onClick={closeSignup}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeSignup}>✕</button>
            <div className="login-header">
              <h1 className="login-title">회원가입</h1>
              <p className="login-subtitle">간단한 정보만 입력하면 됩니다</p>
            </div>
            {signupSuccess ? (
              <div className="signup-success"><div className="success-icon">✅</div><p>회원가입이 완료되었습니다!</p><span>로그인 화면으로 이동합니다...</span></div>
            ) : (
              <form onSubmit={handleSignup} className="login-form">
                <div className="input-group"><label htmlFor="signupId">아이디</label><input id="signupId" type="text" placeholder="사용할 아이디를 입력하세요" value={signupId} onChange={(e) => setSignupId(e.target.value)} /></div>
                <div className="input-group"><label htmlFor="signupPw">비밀번호</label><input id="signupPw" type="password" placeholder="비밀번호를 입력하세요" value={signupPw} onChange={(e) => setSignupPw(e.target.value)} /></div>
                <div className="input-group"><label htmlFor="signupPwConfirm">비밀번호 확인</label><input id="signupPwConfirm" type="password" placeholder="비밀번호를 다시 입력하세요" value={signupPwConfirm} onChange={(e) => setSignupPwConfirm(e.target.value)} /></div>
                {signupError && <p className="login-error">{signupError}</p>}
                <button type="submit" className="login-button">가입하기</button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
export default LoginPage
