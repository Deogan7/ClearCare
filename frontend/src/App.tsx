import { Routes, Route } from "react-router-dom";
import AppShell from "./components/common/AppShell";
import DashboardPage from "./pages/DashboardPage";
import ReferralsPage from "./pages/Referrals/ReferralsPage";
import ReferralDetailPage from "./pages/Referrals/ReferralDetailPage";
import PatientsPage from "./pages/Patients/PatientsPage";
import PatientDetailPage from "./pages/Patients/PatientDetailPage";
import WeatherPage from "./pages/WeatherPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/referrals" element={<ReferralsPage />} />
      <Route path="/referrals/:id" element={<ReferralDetailPage />} />
      <Route path="/patients" element={<PatientsPage />} />
      <Route path="/patients/:id" element={<PatientDetailPage />} />
      <Route path="/weather" element={<WeatherPage />} />
    </Routes>
  );
}

export default App;
