import Card from "../common/Card";
import type { CurrentWeatherResponse } from "../../types/weather";

interface CurrentWeatherCardProps {
  data: CurrentWeatherResponse;
}

function formatNumber(value: number, digits = 1): string {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
}

export default function CurrentWeatherCard({ data }: CurrentWeatherCardProps) {
  const temp = formatNumber(data.temperature_c);
  const snow = formatNumber(data.snow_cm);
  const severityClass = data.is_severe ? "danger" : "ok";
  const severityLabel = data.is_severe ? "severe" : "normal";

  return (
    <Card
      title="Current Conditions"
      action={<span className={`badge ${severityClass}`}>{severityLabel}</span>}
    >
      <div className="stat-value">{temp}°C</div>
      <div className="page-subtitle">{data.description || "No description available."}</div>
      <div className="page-subtitle">Snow: {snow}cm</div>
    </Card>
  );
}
