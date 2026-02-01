import { Routes, Route } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ReferralsPage from "./pages/Referrals/ReferralsPage";
import ReferralDetailPage from "./pages/Referrals/ReferralDetailPage";
import PatientsPage from "./pages/Patients/PatientsPage";
import PatientDetailPage from "./pages/Patients/PatientDetailPage";
import AppointmentsPage from "./pages/Appointments/AppointmentsPage";
import WeatherPage from "./pages/WeatherPage";
import ProtectedRoute from "./components/common/ProtectedRoute";
import Snowfall from "./components/common/Snowfall";

function App() {
  return (
    <>
      <Snowfall />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/referrals" element={<ReferralsPage />} />
          <Route path="/referrals/:id" element={<ReferralDetailPage />} />
          <Route path="/appointments" element={<AppointmentsPage />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/:id" element={<PatientDetailPage />} />
          <Route path="/weather" element={<WeatherPage />} />
        </Route>
      </Routes>
    </>
  );
}

export default App;
