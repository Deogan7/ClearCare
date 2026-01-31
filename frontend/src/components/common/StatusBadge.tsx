interface StatusBadgeProps {
  status: string;
}

const statusClassMap: Record<string, string> = {
  PENDING_CONFIRMATION: "warn",
  SCHEDULED: "info",
  ATTENDED: "ok",
  RESOLVED: "ok",
  MISSED: "danger",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const className = statusClassMap[status] ?? "info";
  const label = status.replace(/_/g, " ").toLowerCase();

  return <span className={`badge ${className}`}>{label}</span>;
}
