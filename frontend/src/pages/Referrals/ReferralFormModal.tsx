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

  if (!open) {
    return null;
  }

  return (
    <Modal>
      <form onSubmit={handleSubmit}>
        <h2>Create Referral</h2>
        {error ? <div>{error}</div> : null}
        <label>
          Patient
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
        <label>
          Description
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
        <label>
          Referred to
          <input
            type="text"
            value={referredTo}
            onChange={(event) => setReferredTo(event.target.value)}
          />
        </label>
        <label>
          Action date
          <input
            type="date"
            value={actionDate}
            onChange={(event) => setActionDate(event.target.value)}
          />
        </label>
        <label>
          Scheduled date
          <input
            type="date"
            value={scheduledDate}
            onChange={(event) => setScheduledDate(event.target.value)}
          />
        </label>
        <label>
          Created by
          <input
            type="text"
            value={createdBy}
            onChange={(event) => setCreatedBy(event.target.value)}
          />
        </label>
        <div>
          <Button type="submit" disabled={!isValid || submitting}>
            {submitting ? "Creating..." : "Create Referral"}
          </Button>
          <Button type="button" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
}
