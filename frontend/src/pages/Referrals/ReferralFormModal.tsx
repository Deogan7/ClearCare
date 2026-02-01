import { useMemo, useState, type FormEvent } from "react";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";
import { createReferral } from "../../services/referralService";
import type { Patient } from "../../types/patient";
import type { ReferralCreatePayload } from "../../types/referral";

interface ReferralFormModalProps {
  open: boolean;
  patients: Patient[];
  onClose: () => void;
  onCreated: () => void;
}

export default function ReferralFormModal({
  open,
  patients,
  onClose,
  onCreated,
}: ReferralFormModalProps) {
  const [patientId, setPatientId] = useState("");
  const [description, setDescription] = useState("");
  const [referredTo, setReferredTo] = useState("");
  const [specialistPhone, setSpecialistPhone] = useState("");
  const [actionDate, setActionDate] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [createdBy, setCreatedBy] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = useMemo(() => {
    return (
      patientId.trim().length > 0 &&
      referredTo.trim().length > 0 &&
      actionDate.trim().length > 0 &&
      createdBy.trim().length > 0
    );
  }, [patientId, referredTo, actionDate, createdBy]);

  const resetForm = () => {
    setPatientId("");
    setDescription("");
    setReferredTo("");
    setSpecialistPhone("");
    setActionDate("");
    setScheduledDate("");
    setCreatedBy("");
    setError(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!isValid || submitting) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const payload: ReferralCreatePayload = {
        patient_id: patientId,
        description: description.trim() ? description.trim() : null,
        referred_to: referredTo.trim(),
        specialist_phone: specialistPhone.trim() ? specialistPhone.trim() : null,
        action_date: actionDate,
        scheduled_date: scheduledDate.trim() ? scheduledDate : null,
        created_by: createdBy.trim(),
      };
      await createReferral(payload);
      resetForm();
      onCreated();
      onClose();
    } catch {
      setError("Unable to create referral. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} title="Create Referral" onClose={onClose}>
      <form onSubmit={handleSubmit} className="form-body">
        {error ? <div className="form-error">{error}</div> : null}
        <label className="form-field">
          <span>Patient *</span>
          <select
            value={patientId}
            onChange={(event) => setPatientId(event.target.value)}
          >
            <option value="">Select a patient</option>
            {patients.map((patient) => (
              <option key={patient.id} value={patient.id}>
                {patient.first_name} {patient.last_name}
              </option>
            ))}
          </select>
        </label>
        <label className="form-field">
          <span>Referred to *</span>
          <input
            type="text"
            placeholder="e.g. Calgary Foothills Cardiology"
            value={referredTo}
            onChange={(event) => setReferredTo(event.target.value)}
          />
        </label>
        <label className="form-field">
          <span>Specialist phone</span>
          <input
            type="tel"
            placeholder="e.g. +14031234567"
            value={specialistPhone}
            onChange={(event) => setSpecialistPhone(event.target.value)}
          />
        </label>
        <label className="form-field">
          <span>Description</span>
          <textarea
            placeholder="Reason for referral..."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <div className="form-row">
          <label className="form-field">
            <span>Action date *</span>
            <input
              type="date"
              value={actionDate}
              onChange={(event) => setActionDate(event.target.value)}
            />
          </label>
          <label className="form-field">
            <span>Scheduled date</span>
            <input
              type="date"
              value={scheduledDate}
              onChange={(event) => setScheduledDate(event.target.value)}
            />
          </label>
        </div>
        <label className="form-field">
          <span>Created by *</span>
          <input
            type="text"
            placeholder="e.g. Nurse Adams"
            value={createdBy}
            onChange={(event) => setCreatedBy(event.target.value)}
          />
        </label>
        <div className="form-actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={!isValid || submitting}>
            {submitting ? "Creating..." : "Create Referral"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
