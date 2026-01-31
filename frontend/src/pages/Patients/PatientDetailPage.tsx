import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Layout from "../../components/common/Layout";
import Table from "../../components/common/Table";
import Button from "../../components/common/Button";
import { getPatient } from "../../services/patientService";
import { getReferrals } from "../../services/referralService";
import type { Patient } from "../../types/patient";
import type { Referral } from "../../types/referral";
import PatientFormModal from "./PatientFormModal";

const STATUS_LABELS: Record<Referral["status"], string> = {
  pending_confirmation: "Pending",
  scheduled: "Scheduled",
  attended: "Attended",
  resolved: "Resolved",
  missed: "Missed",
};

export default function PatientDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    if (!id) {
      setError("Patient ID is missing.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [patientResponse, referralResponse] = await Promise.all([
        getPatient(id),
        getReferrals(),
      ]);
      setPatient(patientResponse.data);
      setReferrals(referralResponse.data);
    } catch {
      setError("Unable to load patient details.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const patientReferrals = useMemo(() => {
    if (!patient) {
      return [];
    }
    return referrals.filter((referral) => referral.patient_id === patient.id);
  }, [patient, referrals]);

  const formatDate = (value: string | null) => {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <Layout>
        <div>Loading patient...</div>
      </Layout>
    );
  }

  if (error || !patient) {
    return (
      <Layout>
        <div>{error ?? "Patient not found."}</div>
        <Button type="button" onClick={() => navigate("/patients")}>
          Back to patients
        </Button>
      </Layout>
    );
  }

  return (
    <Layout>
      <div>
        <Button type="button" onClick={() => navigate("/patients")}>
          Back to patients
        </Button>
        <h1>
          {patient.first_name} {patient.last_name}
        </h1>
        <Button type="button" onClick={() => setIsModalOpen(true)}>
          Edit Patient
        </Button>
        <Table>
          <tbody>
            <tr>
              <th>Phone</th>
              <td>{patient.phone}</td>
            </tr>
            <tr>
              <th>Date of birth</th>
              <td>{patient.date_of_birth ? patient.date_of_birth : "—"}</td>
            </tr>
            <tr>
              <th>Address</th>
              <td>{patient.address ?? "—"}</td>
            </tr>
            <tr>
              <th>High risk</th>
              <td>{patient.is_high_risk ? "Yes" : "No"}</td>
            </tr>
            <tr>
              <th>Notes</th>
              <td>{patient.notes ?? "—"}</td>
            </tr>
          </tbody>
        </Table>
        <h2>Referral history</h2>
        {patientReferrals.length === 0 ? (
          <div>No referrals for this patient.</div>
        ) : (
          <Table>
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Status</th>
                <th>Action date</th>
                <th>Scheduled date</th>
              </tr>
            </thead>
            <tbody>
              {patientReferrals.map((referral) => (
                <tr key={referral.id}>
                  <td>
                    <Button
                      type="button"
                      onClick={() =>
                        navigate(`/referrals/${referral.ticket_id}`)
                      }
                    >
                      {referral.ticket_id}
                    </Button>
                  </td>
                  <td>{STATUS_LABELS[referral.status]}</td>
                  <td>{formatDate(referral.action_date)}</td>
                  <td>{formatDate(referral.scheduled_date)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </div>
      <PatientFormModal
        open={isModalOpen}
        patient={patient}
        onClose={() => setIsModalOpen(false)}
        onSaved={loadData}
      />
    </Layout>
  );
}
