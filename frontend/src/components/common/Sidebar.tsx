import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/" },
  { label: "Referrals", to: "/referrals" },
  { label: "Appointments", to: "/appointments" },
  { label: "Patients", to: "/patients" },
  { label: "Weather", to: "/weather" },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-title">RidgeCare Link</div>
        <div className="sidebar-subtitle">Care coordination console</div>
      </div>
      <nav className="nav-list">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
