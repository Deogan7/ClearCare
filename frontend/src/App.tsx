import { Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import ReferralsPage from "./pages/ReferralsPage";
import PatientsPage from "./pages/PatientsPage";
import WeatherPage from "./pages/WeatherPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/referrals" element={<ReferralsPage />} />
      <Route path="/patients" element={<PatientsPage />} />
      <Route path="/weather" element={<WeatherPage />} />
    </Routes>
  );
}

export default App;
