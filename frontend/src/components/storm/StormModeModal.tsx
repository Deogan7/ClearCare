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
  const {
    isActive,
    status,
    loading,
    activate,
    deactivate,
    wellnessSummary,
    driverNotifications,
  } = useStormMode();
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
        ? `Storm Mode activated. ${count} appointment(s) converted to virtual care. Wellness checks initiating...`
        : "Storm Mode activated. No appointments needed conversion. Wellness checks initiating..."
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

  const wellnessProgress =
    wellnessSummary && wellnessSummary.total > 0
      ? Math.round((wellnessSummary.completed / wellnessSummary.total) * 100)
      : 0;

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
            {/* Conversion stats */}
            <div className="storm-modal-stats">
              <div className="storm-modal-stat">
                <div className="stat-number">{status?.converted_count ?? 0}</div>
                <div className="stat-label">Converted</div>
              </div>
              <div className="storm-modal-stat">
                <div className="stat-number">{status?.window_hours ?? 48}h</div>
                <div className="stat-label">Window</div>
              </div>
              {wellnessSummary && wellnessSummary.total > 0 && (
                <div className="storm-modal-stat">
                  <div className="stat-number">
                    {wellnessSummary.completed}/{wellnessSummary.total}
                  </div>
                  <div className="stat-label">Checked</div>
                </div>
              )}
              {driverNotifications && driverNotifications.total > 0 && (
                <div className="storm-modal-stat">
                  <div className="stat-number">{driverNotifications.total}</div>
                  <div className="stat-label">Drivers Notified</div>
                </div>
              )}
            </div>

            <div className="storm-confirm-banner">
              Storm Mode is active. Triggered{" "}
              <strong>{status?.trigger === "auto" ? "automatically" : "manually"}</strong>
              {status?.activated_by ? ` by ${status.activated_by}` : ""}.
              {status?.activated_at
                ? ` Since ${new Date(status.activated_at).toLocaleString()}.`
                : ""}
            </div>

            {/* Wellness Check Progress */}
            {wellnessSummary && wellnessSummary.total > 0 && (
              <div className="storm-wellness-section">
                <div className="storm-section-header">
                  <strong>Wellness Checks</strong>
                  <span className="badge info">
                    {wellnessSummary.completed}/{wellnessSummary.total}
                  </span>
                </div>

                <div className="storm-progress-bar">
                  <div
                    className="storm-progress-fill"
                    style={{ width: `${wellnessProgress}%` }}
                  />
                </div>

                <div className="storm-wellness-stats">
                  {wellnessSummary.calling > 0 && (
                    <span>Calling: {wellnessSummary.calling}</span>
                  )}
                  <span>Completed: {wellnessSummary.completed}</span>
                  {wellnessSummary.pending > 0 && (
                    <span>Pending: {wellnessSummary.pending}</span>
                  )}
                  {wellnessSummary.failed > 0 && (
                    <span style={{ color: "var(--danger)" }}>
                      Failed: {wellnessSummary.failed}
                    </span>
                  )}
                  {wellnessSummary.skipped > 0 && (
                    <span>Skipped: {wellnessSummary.skipped}</span>
                  )}
                </div>

                {/* Alerts — patients needing attention */}
                {wellnessSummary.alerts.length > 0 && (
                  <div className="storm-alerts-section">
                    <div className="storm-section-header">
                      <strong>Needs Attention</strong>
                      <span className="badge danger">
                        {wellnessSummary.alerts.length}
                      </span>
                    </div>
                    {wellnessSummary.alerts.map((alert) => (
                      <div key={alert.id} className="storm-alert-card">
                        <div className="storm-alert-name">{alert.patient_name}</div>
                        <div className="storm-alert-flags">
                          {alert.has_symptoms && (
                            <span className="badge danger">Symptoms</span>
                          )}
                          {alert.medication_stocked === false && (
                            <span className="badge warn">Low Meds</span>
                          )}
                          {alert.needs_assistance && (
                            <span className="badge info">Needs Help</span>
                          )}
                        </div>
                        {alert.symptom_details && (
                          <div className="storm-alert-detail">
                            {alert.symptom_details}
                          </div>
                        )}
                        {alert.assistance_details && (
                          <div className="storm-alert-detail">
                            {alert.assistance_details}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {wellnessSummary.completed > 0 &&
                  wellnessSummary.alerts.length === 0 &&
                  wellnessSummary.completed === wellnessSummary.total && (
                    <div className="storm-confirm-banner" style={{ marginTop: 8 }}>
                      All wellness checks completed. All patients are doing well.
                    </div>
                  )}
              </div>
            )}

            {/* Driver Notifications */}
            {driverNotifications && driverNotifications.total > 0 && (
              <div className="storm-drivers-section">
                <div className="storm-section-header">
                  <strong>Driver Notifications</strong>
                  <span className="badge info">{driverNotifications.total}</span>
                </div>
                {driverNotifications.notifications.slice(0, 5).map((n) => (
                  <div key={n.id} className="storm-driver-card">
                    <div className="storm-driver-info">
                      <span>{n.patient_name}</span>
                      <span className="page-subtitle">Ticket {n.ticket_id}</span>
                    </div>
                    <span
                      className={`badge ${n.status === "sent" ? "ok" : "info"}`}
                    >
                      {n.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
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
            <div className="storm-confirm-banner" style={{ marginTop: 8 }}>
              High-risk patients will receive an automated wellness check call to
              verify their medication supply and health status.
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
