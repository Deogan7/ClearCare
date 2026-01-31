import AppShell from "../components/common/AppShell";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";

export default function WeatherPage() {
  return (
    <AppShell>
      <div>
        <PageHeader
          title="Weather"
          subtitle="Monitor Storm Mode thresholds and alerts."
          actions={<Button variant="secondary">Refresh</Button>}
        />
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          <Card title="Current Conditions">
            <div className="stat-value">-6°C</div>
            <div className="page-subtitle">Light snow, 1.2cm last 3h</div>
          </Card>
          <Card title="Storm Status" action={<StatusBadge status="SCHEDULED" />}>
            <div className="page-subtitle">Thresholds: -35°C / 15cm</div>
            <div className="stat-value">Clear</div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
