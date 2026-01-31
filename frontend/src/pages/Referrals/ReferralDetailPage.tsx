import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AppShell from "../../components/common/AppShell";
import Button from "../../components/common/Button";
import Table from "../../components/common/Table";
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
      <div>
        <Button type="button" onClick={() => navigate("/referrals")}>
          Back to referrals
        </Button>
        <h1>Referral {referral.ticket_id}</h1>
        <Table>
          <tbody>
            <tr>
              <th>Patient</th>
              <td>
                {patient ? `${patient.first_name} ${patient.last_name}` : "—"}
              </td>
            </tr>
            <tr>
              <th>Status</th>
              <td>{STATUS_LABELS[referral.status]}</td>
            </tr>
            <tr>
              <th>Referred to</th>
              <td>{referral.referred_to}</td>
            </tr>
            <tr>
              <th>Action date</th>
              <td>{formatDate(referral.action_date)}</td>
            </tr>
            <tr>
              <th>Scheduled date</th>
              <td>{formatDate(referral.scheduled_date)}</td>
            </tr>
            <tr>
              <th>Created by</th>
              <td>{referral.created_by}</td>
            </tr>
          </tbody>
        </Table>
        <h2>Status timeline</h2>
        <ul>
          {STATUS_ORDER.map((status) => (
            <li key={status}>
              {STATUS_LABELS[status]}
              {status === referral.status ? " (current)" : ""}
            </li>
          ))}
        </ul>
        <div>
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
        <h2>Update details</h2>
        {updateError ? <div>{updateError}</div> : null}
        <form onSubmit={handleUpdate}>
          <label>
            Scheduled date
            <input
              type="date"
              value={scheduledDate}
              onChange={(event) => setScheduledDate(event.target.value)}
            />
          </label>
          <label>
            Notes
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
            />
          </label>
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save changes"}
          </Button>
        </form>
      </div>
    </AppShell>
  );
}
