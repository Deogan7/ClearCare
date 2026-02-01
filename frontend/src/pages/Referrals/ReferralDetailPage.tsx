import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AppShell from "../../components/common/AppShell";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";
import PageHeader from "../../components/common/PageHeader";
import PatientWorkflowStepper from "../../components/patients/PatientWorkflowStepper";
import { getReferral, updateReferral } from "../../services/referralService";
import { getPatient } from "../../services/patientService";
import type { Patient } from "../../types/patient";
import type { Referral, ReferralStatus } from "../../types/referral";

const STATUS_ORDER: ReferralStatus[] = [
  "pending_confirmation",
  "scheduled",
  "attended",
  "resolved",
  "missed",
];

const STATUS_LABELS: Record<ReferralStatus, string> = {
  pending_confirmation: "Pending",
  scheduled: "Scheduled",
  attended: "Attended",
  resolved: "Resolved",
  missed: "Missed",
};

const STATUS_BADGE_CLASS: Record<ReferralStatus, string> = {
  pending_confirmation: "warn",
  scheduled: "info",
  attended: "ok",
  resolved: "ok",
  missed: "danger",
};

const STATUS_TRANSITIONS: Record<ReferralStatus, ReferralStatus[]> = {
  pending_confirmation: ["scheduled"],
  scheduled: ["attended", "missed"],
  attended: ["resolved"],
  resolved: [],
  missed: [],
};

const toDateInputValue = (value: string | null) => {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toISOString().slice(0, 10);
};

export default function ReferralDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [referral, setReferral] = useState<Referral | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [notes, setNotes] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    const loadReferral = async () => {
      if (!id) {
        setError("Referral ID is missing.");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await getReferral(id);
        if (!isActive) {
          return;
        }
        setReferral(response.data);
        setNotes(response.data.notes ?? "");
        setScheduledDate(toDateInputValue(response.data.scheduled_date));
        if (response.data.patient_id) {
          const patientResponse = await getPatient(response.data.patient_id);
          if (isActive) {
            setPatient(patientResponse.data);
          }
        }
      } catch {
        if (isActive) {
          setError("Unable to load referral details.");
        }
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    };

    void loadReferral();

    return () => {
      isActive = false;
    };
  }, [id]);

  const nextStatuses = useMemo(() => {
    if (!referral) {
      return [];
    }
    return STATUS_TRANSITIONS[referral.status];
  }, [referral]);

  const handleStatusChange = async (nextStatus: ReferralStatus) => {
    if (!referral || saving) {
      return;
    }
    setSaving(true);
    setUpdateError(null);
    try {
      const response = await updateReferral(referral.ticket_id, {
        status: nextStatus,
      });
      setReferral(response.data);
    } catch {
      setUpdateError("Unable to update status.");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (event: FormEvent) => {
    event.preventDefault();
    if (!referral || saving) {
      return;
    }
    setSaving(true);
    setUpdateError(null);
    try {
      const response = await updateReferral(referral.ticket_id, {
        notes: notes.trim() ? notes.trim() : null,
        scheduled_date: scheduledDate.trim() ? scheduledDate : null,
      });
      setReferral(response.data);
    } catch {
      setUpdateError("Unable to update referral.");
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (value: string | null) => {
    if (!value) {
      return "—";
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <AppShell>
        <div>Loading referral...</div>
      </AppShell>
    );
  }

  if (error || !referral) {
    return (
      <AppShell>
        <div>{error ?? "Referral not found."}</div>
        <Button type="button" onClick={() => navigate("/referrals")}>
          Back to referrals
        </Button>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <Button type="button" onClick={() => navigate("/referrals")}>
          Back to referrals
        </Button>

        <PageHeader
          title={`Referral ${referral.ticket_id}`}
          subtitle={
            patient
              ? `${patient.first_name} ${patient.last_name} • ${referral.referred_to}`
              : referral.referred_to
          }
          actions={
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span className={`badge ${STATUS_BADGE_CLASS[referral.status]}`}>
                {STATUS_LABELS[referral.status]}
              </span>
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate("/patients/" + referral.patient_id)}
                disabled={!referral.patient_id}
              >
                View patient
              </Button>
            </div>
          }
        />

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 2fr) minmax(260px, 1fr)",
            gap: 24,
            alignItems: "start",
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <PatientWorkflowStepper referral={referral} />

            <Card title="Next actions">
              {nextStatuses.length === 0 ? (
                <div className="page-subtitle">No status changes available.</div>
              ) : (
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                  {nextStatuses.map((status) => (
                    <Button
                      key={status}
                      type="button"
                      onClick={() => handleStatusChange(status)}
                      disabled={saving}
                    >
                      Mark as {STATUS_LABELS[status]}
                    </Button>
                  ))}
                </div>
              )}
            </Card>

            <Card title="Update details">
              {updateError ? <div className="page-subtitle">{updateError}</div> : null}
              <form onSubmit={handleUpdate}>
                <div style={{ display: "grid", gap: 16, maxWidth: 520 }}>
                  <label>
                    <div style={{ fontWeight: 600, marginBottom: 6 }}>Scheduled date</div>
                    <input
                      type="date"
                      value={scheduledDate}
                      onChange={(event) => setScheduledDate(event.target.value)}
                      style={{ width: "100%" }}
                    />
                  </label>
                  <label>
                    <div style={{ fontWeight: 600, marginBottom: 6 }}>Notes</div>
                    <textarea
                      value={notes}
                      onChange={(event) => setNotes(event.target.value)}
                      style={{ width: "100%", minHeight: 120 }}
                    />
                  </label>
                  <Button type="submit" disabled={saving} style={{ alignSelf: "flex-start" }}>
                    {saving ? "Saving..." : "Save changes"}
                  </Button>
                </div>
              </form>
            </Card>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <Card
              title="Referral summary"
              action={
                <span className={`badge ${STATUS_BADGE_CLASS[referral.status]}`}>
                  {STATUS_LABELS[referral.status]}
                </span>
              }
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div>
                  <div className="page-subtitle">Patient</div>
                  <div>{patient ? `${patient.first_name} ${patient.last_name}` : "—"}</div>
                </div>
                <div>
                  <div className="page-subtitle">Referred to</div>
                  <div>{referral.referred_to}</div>
                </div>
                <div>
                  <div className="page-subtitle">Action date</div>
                  <div>{formatDate(referral.action_date)}</div>
                </div>
                <div>
                  <div className="page-subtitle">Scheduled date</div>
                  <div>{formatDate(referral.scheduled_date)}</div>
                </div>
                <div>
                  <div className="page-subtitle">Created by</div>
                  <div>{referral.created_by}</div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
