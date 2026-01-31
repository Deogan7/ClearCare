import { useEffect, useMemo, useState, type FormEvent } from "react";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";
import {
  createPatient,
  updatePatient,
} from "../../services/patientService";
import type {
  Patient,
  PatientCreatePayload,
  PatientUpdatePayload,
} from "../../types/patient";

interface PatientFormModalProps {
  open: boolean;
  patient?: Patient | null;
  onClose: () => void;
  onSaved: () => void;
}

export default function PatientFormModal({
  open,
  patient,
  onClose,
  onSaved,
}: PatientFormModalProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [address, setAddress] = useState("");
  const [isHighRisk, setIsHighRisk] = useState(false);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patient) {
      setFirstName("");
      setLastName("");
      setPhone("");
      setDateOfBirth("");
      setAddress("");
      setIsHighRisk(false);
      setNotes("");
      setError(null);
      return;
    }
    setFirstName(patient.first_name ?? "");
    setLastName(patient.last_name ?? "");
    setPhone(patient.phone ?? "");
    setDateOfBirth(patient.date_of_birth ?? "");
    setAddress(patient.address ?? "");
    setIsHighRisk(Boolean(patient.is_high_risk));
    setNotes(patient.notes ?? "");
    setError(null);
  }, [patient]);

  const isValid = useMemo(() => {
    return (
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      phone.trim().length > 0
    );
  }, [firstName, lastName, phone]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!isValid || submitting) {
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      if (patient) {
        const payload: PatientUpdatePayload = {
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          phone: phone.trim(),
          date_of_birth: dateOfBirth.trim() ? dateOfBirth : null,
          address: address.trim() ? address.trim() : null,
          is_high_risk: isHighRisk,
          notes: notes.trim() ? notes.trim() : null,
        };
        await updatePatient(patient.id, payload);
      } else {
        const payload: PatientCreatePayload = {
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          phone: phone.trim(),
          date_of_birth: dateOfBirth.trim() ? dateOfBirth : null,
          address: address.trim() ? address.trim() : null,
          is_high_risk: isHighRisk,
          notes: notes.trim() ? notes.trim() : null,
        };
        await createPatient(payload);
      }
      onSaved();
      onClose();
    } catch {
      setError("Unable to save patient.");
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
        <h2>{patient ? "Edit Patient" : "Create Patient"}</h2>
        {error ? <div>{error}</div> : null}
        <label>
          First name
          <input
            type="text"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
          />
        </label>
        <label>
          Last name
          <input
            type="text"
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
          />
        </label>
        <label>
          Phone
          <input
            type="tel"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
        <label>
          Date of birth
          <input
            type="date"
            value={dateOfBirth}
            onChange={(event) => setDateOfBirth(event.target.value)}
          />
        </label>
        <label>
          Address
          <input
            type="text"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
          />
        </label>
        <label>
          High risk
          <input
            type="checkbox"
            checked={isHighRisk}
            onChange={(event) => setIsHighRisk(event.target.checked)}
          />
        </label>
        <label>
          Notes
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
        <div>
          <Button type="submit" disabled={!isValid || submitting}>
            {submitting ? "Saving..." : "Save"}
          </Button>
          <Button type="button" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
}
