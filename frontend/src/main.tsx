import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { StormModeProvider } from "./context/StormModeContext";
import { ToastProvider } from "./components/common/Toast";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <StormModeProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </StormModeProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
