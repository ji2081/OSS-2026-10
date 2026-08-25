import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { supabase } from "./lib/supabaseClient";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState("");
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState("");

  // Supabase 세션 감지 (소셜 로그인 콜백 처리)
  useEffect(() => {
    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        localStorage.setItem("access_token", session.access_token);
        const name =
          session.user.user_metadata?.full_name ||
          session.user.user_metadata?.name ||
          session.user.email?.split("@")[0] ||
          "사용자";
        setUserName(name);
        setIsLoggedIn(true);
      } else if (event === "SIGNED_OUT") {
        setIsLoggedIn(false);
        setUserName("");
      }
      setAuthReady(true);
    });

    // 페이지 새로고침 시 기존 세션 복원
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        setAuthError("로그인 상태를 확인하지 못했습니다. 다시 로그인해주세요.");
      } else if (session) {
        localStorage.setItem("access_token", session.access_token);
        const name =
          session.user.user_metadata?.full_name ||
          session.user.user_metadata?.name ||
          session.user.email?.split("@")[0] ||
          "사용자";
        setUserName(name);
        setIsLoggedIn(true);
      }
      setAuthReady(true);
    }).catch(() => {
      setAuthError("로그인 상태를 확인하지 못했습니다. 다시 로그인해주세요.");
      setAuthReady(true);
    });

    return () => authListener.subscription.unsubscribe();
  }, []);

  const handleLogin = (name) => {
    setAuthError("");
    setIsLoggedIn(true);
    setUserName(name);
  };

  const handleLogout = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      setAuthError("로그아웃에 실패했습니다. 잠시 후 다시 시도해주세요.");
      return;
    }
    localStorage.removeItem("access_token");
    setAuthError("");
    setIsLoggedIn(false);
    setUserName("");
  };

  if (!authReady) {
    return <div className="app-loading" role="status">로그인 상태를 확인하고 있습니다...</div>;
  }

  return (
    <BrowserRouter>
      {authError && isLoggedIn && (
        <div className="app-error-banner" role="alert">{authError}</div>
      )}
      <Routes>
        <Route
          path="/"
          element={
            isLoggedIn ? (
              <Navigate to="/dashboard" />
            ) : (
              <LoginPage onLogin={handleLogin} initialError={authError} />
            )
          }
        />
        <Route
          path="/dashboard"
          element={
            isLoggedIn ? (
              <DashboardPage userName={userName} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
