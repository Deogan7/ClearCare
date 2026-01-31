import { Routes, Route } from "react-router-dom";
import AppShell from "./components/common/AppShell";
import DashboardPage from "./pages/DashboardPage";
import ReferralsPage from "./pages/ReferralsPage";
import PatientsPage from "./pages/PatientsPage";
import WeatherPage from "./pages/WeatherPage";

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/referrals" element={<ReferralsPage />} />
        <Route path="/patients" element={<PatientsPage />} />
        <Route path="/weather" element={<WeatherPage />} />
      </Routes>
    </AppShell>
  );
}

export default App;
