import Card from "../common/Card";
import type { Referral } from "../../types/referral";

interface PatientWorkflowStepperProps {
  referral: Referral | null;
}

type Step = {
  key: string;
  label: string;
  caption: string;
};

const STEPS: Step[] = [
  {
    key: "referral_created",
    label: "Referral created",
    caption: "Initial intake recorded",
  },
  {
    key: "referral_sent",
    label: "Sent to specialist",
    caption: "Awaiting confirmation",
  },
  {
    key: "appointment_scheduled",
    label: "Appointment scheduled",
    caption: "Visit date confirmed",
  },
  {
    key: "visit_attended",
    label: "Visit attended",
    caption: "Care delivered",
  },
  {
    key: "followup_complete",
    label: "Follow-up complete",
    caption: "Case closed",
  },
];

const STATUS_TO_INDEX: Record<Referral["status"], number> = {
  pending_confirmation: 1,
  scheduled: 2,
  attended: 3,
  resolved: 4,
  missed: 2,
};

export default function PatientWorkflowStepper({ referral }: PatientWorkflowStepperProps) {
  if (!referral) {
    return (
      <Card title="Care workflow">
        <div className="page-subtitle">No referral history yet.</div>
      </Card>
    );
  }

  const currentIndex = STATUS_TO_INDEX[referral.status];

  return (
    <Card
      title="Care workflow"
      action={
        referral.status === "missed" ? (
          <span className="badge warn">missed appointment</span>
        ) : null
      }
    >
      <div style={{ display: "flex", flexWrap: "wrap", gap: 16 }}>
        {STEPS.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index == currentIndex;
          const background = isComplete
            ? "var(--ok)"
            : isCurrent
            ? referral.status === "missed"
              ? "var(--warn)"
              : "var(--info)"
            : "var(--surface-2)";
          const color = isComplete || isCurrent ? "#ffffff" : "var(--muted)";
          const borderColor = isComplete || isCurrent ? background : "var(--border)";

          return (
            <div key={step.key} style={{ display: "flex", gap: 10, minWidth: 180 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  background,
                  color,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: `1px solid ${borderColor}`,
                  fontWeight: 600,
                  fontSize: 13,
                  flexShrink: 0,
                }}
              >
                {index + 1}
              </div>
              <div>
                <div style={{ fontWeight: 600 }}>{step.label}</div>
                <div className="page-subtitle">{step.caption}</div>
              </div>
            </div>
          );
        })}
      </div>
      {referral.status === "missed" ? (
        <div className="page-subtitle" style={{ marginTop: 12 }}>
          Follow-up is required to reschedule this appointment.
        </div>
      ) : null}
    </Card>
  );
}
