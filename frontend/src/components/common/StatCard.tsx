import Card from "./Card";

interface StatCardProps {
  label: string;
  value: string;
  helper?: string;
}

export default function StatCard({ label, value, helper }: StatCardProps) {
  return (
    <Card>
      <div className="stat-card">
        <span className="page-subtitle">{label}</span>
        <span className="stat-value">{value}</span>
        {helper ? <span className="page-subtitle">{helper}</span> : null}
      </div>
    </Card>
  );
}
