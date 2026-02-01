import Card from "../common/Card";
import type { Referral } from "../../types/referral";

interface PatientWorkflowStepperProps {
  referral: Referral | null;
}

type Step = {
  key: string;
  label: string;
  caption: string;
  icon: string;
};

const STEPS: Step[] = [
  {
    key: "referral_created",
    label: "Referral created",
    caption: "Initial intake recorded",
    icon: "📋",
  },
  {
    key: "sent_to_specialist",
    label: "Sent to specialist",
    caption: "Awaiting confirmation",
    icon: "📨",
  },
  {
    key: "referral_received",
    label: "Referral received",
    caption: "Specialist confirmed",
    icon: "✅",
  },
  {
    key: "appointment_scheduled",
    label: "Appointment scheduled",
    caption: "Visit date confirmed",
    icon: "📅",
  },
  {
    key: "patient_notified",
    label: "Patient notified",
    caption: "Patient aware of visit",
    icon: "📞",
  },
  {
    key: "completed",
    label: "Visit completed",
    caption: "Care delivered",
    icon: "🏥",
  },
  {
    key: "closed",
    label: "Case closed",
    caption: "Ticket resolved",
    icon: "🔒",
  },
];

const STATUS_TO_INDEX: Record<Referral["status"], number> = {
  sent_to_specialist: 1,
  resent_to_specialist: 1,
  referral_received: 2,
  appointment_scheduling: 3,
  appointment_scheduled: 3,
  patient_notified: 4,
  completed: 5,
  missed: 4,
  reschedule_requested: 3,
  closed: 6,
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
  const isMissed = referral.status === "missed";
  const isReschedule = referral.status === "reschedule_requested";

  return (
    <Card
      title="Care workflow"
      action={
        isMissed ? (
          <span className="badge danger">Missed appointment</span>
        ) : isReschedule ? (
          <span className="badge warn">Reschedule requested</span>
        ) : null
      }
    >
      <div className="workflow-stepper">
        {STEPS.map((step, index) => {
          const isComplete = index < currentIndex;
          const isCurrent = index === currentIndex;
          const stepClass = isComplete
            ? "step-complete"
            : isCurrent
            ? isMissed
              ? "step-missed"
              : "step-current"
            : "step-pending";

          return (
            <div key={step.key} className={`workflow-step ${stepClass}`}>
              <div className="step-node">
                {isComplete ? "✓" : step.icon}
              </div>
              <div className="step-label">{step.label}</div>
              <div className="step-caption">{step.caption}</div>
            </div>
          );
        })}
      </div>
      {isMissed ? (
        <div className="workflow-alert alert-danger">
          ⚠ Follow-up is required to reschedule this appointment.
        </div>
      ) : isReschedule ? (
        <div className="workflow-alert alert-warn">
          ↻ Patient has requested a reschedule — awaiting new appointment date.
        </div>
      ) : null}
    </Card>
  );
}
