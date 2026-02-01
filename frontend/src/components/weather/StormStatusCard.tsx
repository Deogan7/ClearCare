import Card from "../common/Card";
import type { StormStatusResponse } from "../../types/weather";

interface StormStatusCardProps {
  data: StormStatusResponse;
}

function formatNumber(value: number, digits = 1): string {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
}

export default function StormStatusCard({ data }: StormStatusCardProps) {
  const statusClass = data.is_severe ? "danger" : "ok";
  const statusLabel = data.is_severe ? "severe" : "clear";
  const thresholdTemp = formatNumber(data.thresholds?.temp_c);
  const thresholdSnow = formatNumber(data.thresholds?.snow_cm);

  return (
    <Card
      title="Storm Status"
      action={<span className={`badge ${statusClass}`}>{statusLabel}</span>}
    >
      <div className="stat-value">{statusLabel}</div>
      <div className="page-subtitle">
        Thresholds: temp ≤ {thresholdTemp}°C or snow ≥ {thresholdSnow}cm
      </div>
    </Card>
  );
}
