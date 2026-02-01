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
  sent_to_specialist: "Sent to Specialist",
  resent_to_specialist: "Resent to Specialist",
  referral_received: "Referral Received",
  appointment_scheduling: "Scheduling",
  appointment_scheduled: "Scheduled",
  patient_notified: "Patient Notified",
  completed: "Completed",
  missed: "Missed",
  reschedule_requested: "Reschedule Requested",
  closed: "Closed",
};

const STATUS_OPTIONS: Array<{ value: ReferralStatus | "all"; label: string }> =
  [
    { value: "all", label: "All statuses" },
    { value: "sent_to_specialist", label: "Sent to Specialist" },
    { value: "resent_to_specialist", label: "Resent to Specialist" },
    { value: "referral_received", label: "Referral Received" },
    { value: "appointment_scheduling", label: "Scheduling" },
    { value: "appointment_scheduled", label: "Scheduled" },
    { value: "patient_notified", label: "Patient Notified" },
    { value: "completed", label: "Completed" },
    { value: "missed", label: "Missed" },
    { value: "reschedule_requested", label: "Reschedule Requested" },
    { value: "closed", label: "Closed" },
  ];

const STATUS_ROW_COLOR: Record<ReferralStatus, string> = {
  sent_to_specialist: "#fef3c7",      // warm amber — awaiting action
  resent_to_specialist: "#fde68a",    // deeper amber — needs attention
  referral_received: "#dbeafe",       // light blue — acknowledged
  appointment_scheduling: "#e0e7ff",  // soft indigo — in progress
  appointment_scheduled: "#c7d2fe",   // indigo — confirmed
  patient_notified: "#d1fae5",        // light green — on track
  completed: "#a7f3d0",              // green — done
  missed: "#fecaca",                 // light red — action needed
  reschedule_requested: "#fed7aa",   // light orange — pending reschedule
  closed: "#e5e7eb",                 // neutral grey — resolved
};

type PriorityLevel = "immediate" | "high" | "standard" | "deferred";

const PRIORITY_LABELS: Record<PriorityLevel, string> = {
  immediate: "Immediate",
  high: "High",
  standard: "Standard",
  deferred: "Deferred",
};

const PRIORITY_TARGETS: Record<PriorityLevel, string> = {
  immediate: "≤ 24h",
  high: "≤ 72h",
  standard: "≤ 7d",
  deferred: "7+ days",
};

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

  const patientHighRiskById = useMemo(() => {
    const map = new Map<string, boolean>();
    if (!Array.isArray(patients)) {
      return map;
    }
    patients.forEach((patient) => {
      map.set(patient.id, Boolean(patient.is_high_risk));
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

  const getPriority = (referral: Referral): PriorityLevel => {
    const actionDate = referral.action_date ? new Date(referral.action_date) : null;
    if (!actionDate || Number.isNaN(actionDate.getTime())) {
      return "deferred";
    }
    const now = new Date();
    const diffMs = actionDate.getTime() - now.getTime();
    const diffHours = diffMs / 3600000;

    if (diffHours <= 24) {
      return "immediate";
    }
    if (diffHours <= 72) {
      return "high";
    }
    if (diffHours <= 168) {
      return "standard";
    }
    return "deferred";
  };

  const priorityRank: Record<PriorityLevel, number> = {
    immediate: 0,
    high: 1,
    standard: 2,
    deferred: 3,
  };

  const sortedReferrals = useMemo(() => {
    const activeReferrals = filteredReferrals.filter(
      (referral) => referral.status !== "closed"
    );
    const resolvedReferrals = filteredReferrals.filter(
      (referral) => referral.status === "closed"
    );
    const sortByPriority = (items: Referral[]) =>
      [...items].sort((a, b) => {
        const rankA = priorityRank[getPriority(a)];
        const rankB = priorityRank[getPriority(b)];
        if (rankA !== rankB) {
          return rankA - rankB;
        }
        const dateA = a.action_date
          ? new Date(a.action_date).getTime()
          : Number.MAX_SAFE_INTEGER;
        const dateB = b.action_date
          ? new Date(b.action_date).getTime()
          : Number.MAX_SAFE_INTEGER;
        return dateA - dateB;
      });
    return [...sortByPriority(activeReferrals), ...sortByPriority(resolvedReferrals)];
  }, [filteredReferrals]);

  const priorityDot = (level: PriorityLevel, resolved = false) => {
    const color = resolved
      ? "#98a2b3"
      : level === "immediate"
      ? "#d14343"
      : level === "high"
      ? "#d17c43"
      : level === "standard"
      ? "#d1a943"
      : "#2f9a5a";
    return (
      <span
        aria-hidden
        style={{
          display: "inline-block",
          width: 10,
          height: 10,
          borderRadius: "50%",
          backgroundColor: color,
          marginRight: 8,
        }}
      />
    );
  };

  return (
    <AppShell>
      <div>
        <h1>Referrals</h1>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
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
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {(["immediate", "high", "standard", "deferred"] as PriorityLevel[]).map((level) => (
              <div key={level} style={{ display: "flex", alignItems: "center" }}>
                {priorityDot(level)}
                <span className="page-subtitle">
                  {PRIORITY_LABELS[level]} ({PRIORITY_TARGETS[level]})
                </span>
              </div>
            ))}
          </div>
        </div>
        {loading ? <div>Loading referrals...</div> : null}
        {error ? <div>{error}</div> : null}
        {!loading && !error && filteredReferrals.length === 0 ? (
          <div>No referrals found.</div>
        ) : null}
        {!loading && !error && filteredReferrals.length > 0 ? (
          <Table
            headers={[
              "Priority",
              "Ticket ID",
              "Patient name",
              "Status",
              "Referred to",
              "Scheduled date",
              "Action date",
            ]}
          >
              {sortedReferrals.map((referral) => (
                <tr
                  key={referral.id}
                  style={{
                    backgroundColor: STATUS_ROW_COLOR[referral.status] + "40",
                    borderLeft: `4px solid ${STATUS_ROW_COLOR[referral.status]}`,
                  }}
                >
                  <td>
                    <span style={{ display: "flex", alignItems: "center" }}>
                      {priorityDot(getPriority(referral), referral.status === "closed")}
                      <span className="page-subtitle">
                        {PRIORITY_LABELS[getPriority(referral)]}
                      </span>
                    </span>
                  </td>
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
