import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../../components/common/AppShell";
import Table from "../../components/common/Table";
import Button from "../../components/common/Button";
import { getReferrals } from "../../services/referralService";
import { getPatients } from "../../services/patientService";
import type { Patient } from "../../types/patient";
import type { Referral, ReferralStatus } from "../../types/referral";
import ReferralFormModal from "./ReferralFormModal";

const STATUS_LABELS: Record<ReferralStatus, string> = {
  pending_confirmation: "Pending",
  scheduled: "Scheduled",
  attended: "Attended",
  resolved: "Resolved",
  missed: "Missed",
};

const STATUS_OPTIONS: Array<{ value: ReferralStatus | "all"; label: string }> =
  [
    { value: "all", label: "All statuses" },
    { value: "pending_confirmation", label: "Pending" },
    { value: "scheduled", label: "Scheduled" },
    { value: "attended", label: "Attended" },
    { value: "resolved", label: "Resolved" },
    { value: "missed", label: "Missed" },
  ];

export default function ReferralsPage() {
  const navigate = useNavigate();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [statusFilter, setStatusFilter] = useState<ReferralStatus | "all">(
    "all"
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [referralResponse, patientResponse] = await Promise.all([
        getReferrals(),
        getPatients(),
      ]);
      setReferrals(
        Array.isArray(referralResponse.data) ? referralResponse.data : []
      );
      setPatients(
        Array.isArray(patientResponse.data) ? patientResponse.data : []
      );
    } catch {
      setError("Unable to load referrals.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const patientNameById = useMemo(() => {
    const map = new Map<string, string>();
    if (!Array.isArray(patients)) {
      return map;
    }
    patients.forEach((patient) => {
      map.set(patient.id, `${patient.first_name} ${patient.last_name}`);
    });
    return map;
  }, [patients]);

  const filteredReferrals = useMemo(() => {
    if (!Array.isArray(referrals)) {
      return [];
    }
    if (statusFilter === "all") {
      return referrals;
    }
    return referrals.filter((referral) => referral.status === statusFilter);
  }, [referrals, statusFilter]);

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

  return (
    <AppShell>
      <div>
        <h1>Referrals</h1>
        <div>
          <label>
            Status
            <select
              value={statusFilter}
              onChange={(event) =>
                setStatusFilter(event.target.value as ReferralStatus | "all")
              }
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <Button type="button" onClick={() => setIsModalOpen(true)}>
            New Referral
          </Button>
        </div>
        {loading ? <div>Loading referrals...</div> : null}
        {error ? <div>{error}</div> : null}
        {!loading && !error && filteredReferrals.length === 0 ? (
          <div>No referrals found.</div>
        ) : null}
        {!loading && !error && filteredReferrals.length > 0 ? (
          <Table headers={["Ticket ID", "Patient name", "Status", "Referred to", "Scheduled date", "Action date"]}>
              {filteredReferrals.map((referral) => (
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
                  <td>{patientNameById.get(referral.patient_id) ?? "Unknown"}</td>
                  <td>{STATUS_LABELS[referral.status]}</td>
                  <td>{referral.referred_to}</td>
                  <td>{formatDate(referral.scheduled_date)}</td>
                  <td>{formatDate(referral.action_date)}</td>
                </tr>
              ))}
          </Table>
        ) : null}
      </div>
      <ReferralFormModal
        open={isModalOpen}
        patients={patients}
        onClose={() => setIsModalOpen(false)}
        onCreated={loadData}
      />
    </AppShell>
  );
}
