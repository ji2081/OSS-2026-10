// main.jsx — React 앱의 시작점
// ReactDOM.createRoot()로 index.html의 <div id="root">에 React를 연결함
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

const observer = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends observer {
  constructor(callback) {
    super((entries, observer) => {
      requestAnimationFrame(() => {
        callback(entries, observer);
      });
    });
  }
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
