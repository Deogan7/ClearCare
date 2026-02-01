import { useState, useMemo, type FormEvent } from "react";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";
import { createAppointment } from "../../services/appointmentService";
import type { AppointmentCreatePayload, RiskLevel } from "../../types/appointment";
import type { Patient } from "../../types/patient";

interface AppointmentFormModalProps {
  open: boolean;
  patients: Patient[];
  onClose: () => void;
  onCreated: () => void;
}

export default function AppointmentFormModal({
  open,
  patients,
  onClose,
  onCreated,
}: AppointmentFormModalProps) {
  const [patientId, setPatientId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [riskLevel, setRiskLevel] = useState<RiskLevel>("low");
  const [appointmentDate, setAppointmentDate] = useState("");
  const [appointmentTime, setAppointmentTime] = useState("09:00");
  const [duration, setDuration] = useState("30");
  const [provider, setProvider] = useState("");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = useMemo(
    () =>
      patientId.trim().length > 0 &&
      title.trim().length > 0 &&
      appointmentDate.trim().length > 0 &&
      provider.trim().length > 0,
    [patientId, title, appointmentDate, provider]
  );

  const resetForm = () => {
    setPatientId("");
    setTitle("");
    setDescription("");
    setRiskLevel("low");
    setAppointmentDate("");
    setAppointmentTime("09:00");
    setDuration("30");
    setProvider("");
    setLocation("");
    setNotes("");
    setError(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!isValid || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      const dateTime = `${appointmentDate}T${appointmentTime}:00`;
      const payload: AppointmentCreatePayload = {
        patient_id: patientId,
        title: title.trim(),
        description: description.trim() || null,
        risk_level: riskLevel,
        appointment_date: dateTime,
        duration_minutes: parseInt(duration, 10) || 30,
        provider: provider.trim(),
        location: location.trim() || null,
        notes: notes.trim() || null,
      };
      await createAppointment(payload);
      resetForm();
      onCreated();
      onClose();
    } catch {
      setError("Unable to create appointment. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal open={open} title="New Appointment" onClose={handleClose}>
      <form onSubmit={handleSubmit} className="form-body">
        {error && <div className="form-error">{error}</div>}

        <label className="form-field">
          <span>Patient *</span>
          <select
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
          >
            <option value="">Select a patient</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.first_name} {p.last_name}
              </option>
            ))}
          </select>
        </label>

        <label className="form-field">
          <span>Title *</span>
          <input
            type="text"
            placeholder="e.g. Annual Physical, Follow-up, Lab Work"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>

        <label className="form-field">
          <span>Description</span>
          <textarea
            placeholder="Brief description of the appointment purpose"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>

        <div className="form-row">
          <label className="form-field">
            <span>Risk Level</span>
            <select
              value={riskLevel}
              onChange={(e) => setRiskLevel(e.target.value as RiskLevel)}
            >
              <option value="low">Low</option>
              <option value="moderate">Moderate</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>
          <label className="form-field">
            <span>Provider *</span>
            <input
              type="text"
              placeholder="Dr. Name"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            />
          </label>
        </div>

        <div className="form-row">
          <label className="form-field">
            <span>Date *</span>
            <input
              type="date"
              value={appointmentDate}
              onChange={(e) => setAppointmentDate(e.target.value)}
            />
          </label>
          <label className="form-field">
            <span>Time</span>
            <input
              type="text"
              placeholder="09:00"
              value={appointmentTime}
              onChange={(e) => setAppointmentTime(e.target.value)}
            />
          </label>
        </div>

        <div className="form-row">
          <label className="form-field">
            <span>Duration (minutes)</span>
            <input
              type="text"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </label>
          <label className="form-field">
            <span>Location</span>
            <input
              type="text"
              placeholder="Room 101"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </label>
        </div>

        <label className="form-field">
          <span>Notes</span>
          <textarea
            placeholder="Any additional notes..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>

        <div className="form-actions">
          <Button variant="ghost" type="button" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={!isValid || submitting}>
            {submitting ? "Creating..." : "Create Appointment"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
