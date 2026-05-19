// // App.jsx — 앱의 뼈대. 페이지 라우팅(URL에 따라 다른 페이지 보여주기)을 담당
// //
// // [핵심 개념] React Router
// // - <BrowserRouter>: URL 변경을 감지하는 컨테이너
// // - <Routes>: "이 URL이면 이 컴포넌트를 보여줘" 라는 규칙 모음
// // - <Route path="/" element={<LoginPage />}>: "/" 주소면 LoginPage를 보여줌

// import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
// import { useState } from "react";
// import LoginPage from "./pages/LoginPage";
// import DashboardPage from "./pages/DashboardPage";

// function App() {
//   // [핵심 개념] useState — React에서 "변하는 값"을 관리하는 방법
//   // isLoggedIn이 바뀌면 화면이 자동으로 다시 그려짐 (re-render)
//   const [isLoggedIn, setIsLoggedIn] = useState(false);
//   const [userName, setUserName] = useState("");

//   // 로그인 처리 함수 — LoginPage에서 호출됨
//   const handleLogin = (name) => {
//     setIsLoggedIn(true);
//     setUserName(name);
//   };

//   // 로그아웃 처리 함수
//   const handleLogout = () => {
//     setIsLoggedIn(false);
//     setUserName("");
//   };

//   return (
//     <BrowserRouter>
//       <Routes>
//         {/* 로그인 페이지 */}
//         <Route
//           path="/"
//           element={
//             isLoggedIn ? (
//               <Navigate to="/dashboard" /> // 이미 로그인됐으면 대시보드로 이동
//             ) : (
//               <LoginPage onLogin={handleLogin} />
//             )
//           }
//         />

//         {/* 대시보드 페이지 */}
//         <Route
//           path="/dashboard"
//           element={
//             isLoggedIn ? (
//               <DashboardPage userName={userName} onLogout={handleLogout} />
//             ) : (
//               <Navigate to="/" />
//             ) // 로그인 안 했으면 로그인 페이지로
//           }
//         />

//         {/* TODO: 간트 차트 로드맵 페이지 (나중에 추가) */}
//         {/* <Route path="/roadmap" element={<RoadmapPage />} /> */}
//       </Routes>
//     </BrowserRouter>
//   );
// }

// export default App; // 이전 app

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { supabase } from "./lib/supabaseClient";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userName, setUserName] = useState("");

  // Supabase 세션 감지 (소셜 로그인 콜백 처리)
  useEffect(() => {
    supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        localStorage.setItem("access_token", session.access_token);
        const name =
          session.user.user_metadata?.full_name ||
          session.user.user_metadata?.name ||
          session.user.email?.split("@")[0] ||
          "사용자";
        setUserName(name);
        setIsLoggedIn(true);
      }
    });

    // 페이지 새로고침 시 기존 세션 복원
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        localStorage.setItem("access_token", session.access_token);
        const name =
          session.user.user_metadata?.full_name ||
          session.user.user_metadata?.name ||
          session.user.email?.split("@")[0] ||
          "사용자";
        setUserName(name);
        setIsLoggedIn(true);
      }
    });
  }, []);

  const handleLogin = (name) => {
    setIsLoggedIn(true);
    setUserName(name);
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
    setUserName("");
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            isLoggedIn ? (
              <Navigate to="/dashboard" />
            ) : (
              <LoginPage onLogin={handleLogin} />
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
