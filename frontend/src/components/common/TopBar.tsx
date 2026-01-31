import { useLocation } from "react-router-dom";

const titles: Record<string, string> = {
  "/": "Dashboard",
  "/referrals": "Referrals",
  "/patients": "Patients",
  "/weather": "Weather",
};

export default function TopBar() {
  const location = useLocation();
  const title = titles[location.pathname] ?? "RidgeCare";

  return (
    <header className="topbar">
      <div className="topbar-title">{title}</div>
      <div className="topbar-meta">
        <span className="env-pill">DEV</span>
        <span className="user-pill">Nurse Console</span>
      </div>
    </header>
  );
}
