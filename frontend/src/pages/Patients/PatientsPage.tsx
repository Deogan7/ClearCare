import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/common/AppShell";
import Table from "../../components/common/Table";
import Button from "../../components/common/Button";
import { getPatients } from "../../services/patientService";
import { getReferrals } from "../../services/referralService";
import type { Patient } from "../../types/patient";
import type { Referral } from "../../types/referral";
import PatientFormModal from "./PatientFormModal";

export default function PatientsPage() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientResponse, referralResponse] = await Promise.all([
        getPatients(),
        getReferrals(),
      ]);
      setPatients(Array.isArray(patientResponse.data) ? patientResponse.data : []);
      setReferrals(Array.isArray(referralResponse.data) ? referralResponse.data : []);
    } catch {
      setError("Unable to load patients.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const activeReferralCounts = useMemo(() => {
    const counts = new Map<string, number>();
    if (!Array.isArray(referrals)) {
      return counts;
    }
    referrals.forEach((referral) => {
      if (referral.status !== "resolved") {
        counts.set(
          referral.patient_id,
          (counts.get(referral.patient_id) ?? 0) + 1
        );
      }
    });
    return counts;
  }, [referrals]);

  return (
    <AppShell>
      <div>
        <h1>Patients</h1>
        <div>
          <Button type="button" onClick={() => setIsModalOpen(true)}>
            New Patient
          </Button>
        </div>
        {loading ? <div>Loading patients...</div> : null}
        {error ? <div>{error}</div> : null}
        {!loading && !error && patients.length === 0 ? (
          <div>No patients found.</div>
        ) : null}
        {!loading && !error && patients.length > 0 ? (
          <Table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>High-risk flag</th>
                <th>Active referrals</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td>
                    <Button
                      type="button"
                      onClick={() => navigate(`/patients/${patient.id}`)}
                    >
                      {patient.first_name} {patient.last_name}
                    </Button>
                  </td>
                  <td>{patient.phone}</td>
                  <td>{patient.is_high_risk ? "Yes" : "No"}</td>
                  <td>{activeReferralCounts.get(patient.id) ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : null}
      </div>
      <PatientFormModal
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSaved={loadData}
      />
    </AppShell>
  );
}
