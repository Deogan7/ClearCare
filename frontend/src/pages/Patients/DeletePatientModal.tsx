import { useState } from "react";
import Modal from "../../components/common/Modal";
import Button from "../../components/common/Button";
import { deletePatient } from "../../services/patientService";
import type { Patient } from "../../types/patient";

interface DeletePatientModalProps {
  open: boolean;
  patient: Patient | null;
  onClose: () => void;
  onDeleted: () => void;
}

export default function DeletePatientModal({
  open,
  patient,
  onClose,
  onDeleted,
}: DeletePatientModalProps) {
  const [confirmation, setConfirmation] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canDelete = confirmation.toLowerCase() === "delete";

  const handleClose = () => {
    setConfirmation("");
    setError(null);
    onClose();
  };

  const handleDelete = async () => {
    if (!canDelete || !patient || deleting) return;
    setDeleting(true);
    setError(null);
    try {
      await deletePatient(patient.id);
      setConfirmation("");
      onDeleted();
      onClose();
    } catch {
      setError("Unable to delete patient. They may have existing referrals.");
    } finally {
      setDeleting(false);
    }
  };

  if (!patient) return null;

  return (
    <Modal open={open} title="Delete Patient" onClose={handleClose}>
      <div className="form-body">
        <div className="delete-warning">
          <p>
            You are about to permanently delete{" "}
            <strong>
              {patient.first_name} {patient.last_name}
            </strong>{" "}
            and all associated data. This action cannot be undone.
          </p>
          <p>
            To confirm, type <strong>delete</strong> in the box below.
          </p>
        </div>
        {error ? <div className="form-error">{error}</div> : null}
        <label className="form-field">
          <span>Type "delete" to confirm</span>
          <input
            type="text"
            placeholder="delete"
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            autoComplete="off"
          />
        </label>
        <div className="form-actions">
          <Button type="button" variant="ghost" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="button"
            variant="danger"
            disabled={!canDelete || deleting}
            onClick={handleDelete}
          >
            {deleting ? "Deleting..." : "Delete Patient"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
