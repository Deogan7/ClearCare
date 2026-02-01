import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { useStormMode } from "../../context/StormModeContext";
import StormModeModal from "../storm/StormModeModal";

const titles: Record<string, string> = {
  "/": "Dashboard",
  "/referrals": "Referrals",
  "/patients": "Patients",
  "/weather": "Weather",
};

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isActive } = useStormMode();
  const [stormModalOpen, setStormModalOpen] = useState(false);
  const title = titles[location.pathname] ?? "RidgeCare";

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <>
      <header className="topbar">
        <div className="topbar-title">{title}</div>
        <div className="topbar-meta">
          <button
            className={`storm-indicator ${isActive ? "active" : "inactive"}`}
            onClick={() => setStormModalOpen(true)}
          >
            <span className="storm-dot" />
            {isActive ? "Storm Active" : "Storm Mode"}
          </button>
          <span className="env-pill">DEV</span>
          <span className="user-pill">{user?.role ?? "nurse"}</span>
          <button className="button ghost" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>
      <StormModeModal open={stormModalOpen} onClose={() => setStormModalOpen(false)} />
    </>
  );
}
