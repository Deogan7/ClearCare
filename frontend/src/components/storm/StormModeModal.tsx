import { useCallback, useEffect, useState } from "react";
import Modal from "../common/Modal";
import Button from "../common/Button";
import { useStormMode } from "../../context/StormModeContext";
import { previewConversions } from "../../services/weatherService";

interface StormModeModalProps {
  open: boolean;
  onClose: () => void;
}

export default function StormModeModal({ open, onClose }: StormModeModalProps) {
  const { isActive, status, loading, activate, deactivate } = useStormMode();
  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  const loadPreview = useCallback(async () => {
    if (!isActive && open) {
      try {
        const preview = await previewConversions(48);
        setPreviewCount(preview.count);
      } catch {
        setPreviewCount(null);
      }
    }
  }, [isActive, open]);

  useEffect(() => {
    void loadPreview();
    setResultMessage(null);
  }, [loadPreview]);

  const handleActivate = async () => {
    const count = await activate(48);
    setResultMessage(
      count > 0
        ? `Storm Mode activated. ${count} appointment(s) converted to virtual care.`
        : "Storm Mode activated. No appointments needed conversion."
    );
  };

  const handleDeactivate = async () => {
    await deactivate();
    setResultMessage("Storm Mode deactivated.");
    setTimeout(() => {
      setResultMessage(null);
      onClose();
    }, 1500);
  };

  return (
    <Modal
      open={open}
      title={isActive ? "Storm Mode Active" : "Activate Storm Mode"}
      onClose={onClose}
    >
      <div className="storm-modal-content">
        <div className="storm-modal-icon">
          {isActive ? "\u26A1" : "\u2744\uFE0F"}
        </div>

        {resultMessage ? (
          <div className="storm-confirm-banner">{resultMessage}</div>
        ) : isActive ? (
          <>
            <div className="storm-modal-stats">
              <div className="storm-modal-stat">
                <div className="stat-number">{status?.converted_count ?? 0}</div>
                <div className="stat-label">Converted</div>
              </div>
              <div className="storm-modal-stat">
                <div className="stat-number">{status?.window_hours ?? 48}h</div>
                <div className="stat-label">Window</div>
              </div>
            </div>
            <div className="storm-confirm-banner">
              Storm Mode is active. Triggered{" "}
              <strong>{status?.trigger === "auto" ? "automatically" : "manually"}</strong>
              {status?.activated_by ? ` by ${status.activated_by}` : ""}.
              {status?.activated_at
                ? ` Since ${new Date(status.activated_at).toLocaleString()}.`
                : ""}
            </div>
          </>
        ) : (
          <>
            <div className="storm-modal-stats">
              <div className="storm-modal-stat">
                <div className="stat-number">{previewCount ?? "..."}</div>
                <div className="stat-label">To convert</div>
              </div>
              <div className="storm-modal-stat">
                <div className="stat-number">48h</div>
                <div className="stat-label">Window</div>
              </div>
            </div>
            <div className="storm-confirm-banner">
              This will convert <strong>{previewCount ?? "..."} upcoming in-person
              appointments</strong> to virtual care within the next 48 hours. Only
              non-urgent, scheduled appointments are affected.
            </div>
          </>
        )}

        <div className="form-actions">
          <Button variant="ghost" onClick={onClose}>
            {isActive ? "Close" : "Cancel"}
          </Button>
          {isActive ? (
            <Button variant="danger" onClick={handleDeactivate} disabled={loading}>
              {loading ? "Deactivating..." : "Deactivate Storm Mode"}
            </Button>
          ) : !resultMessage ? (
            <Button variant="primary" onClick={handleActivate} disabled={loading}>
              {loading ? "Activating..." : "Activate Storm Mode"}
            </Button>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
