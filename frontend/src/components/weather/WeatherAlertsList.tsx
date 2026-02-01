import Card from "../common/Card";
import Table from "../common/Table";
import type { WeatherAlert } from "../../types/weather";

interface WeatherAlertsListProps {
  alerts: WeatherAlert[];
}

function getString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function getFirstString(alert: WeatherAlert, keys: string[]): string {
  for (const key of keys) {
    const value = getString(alert[key]);
    if (value) {
      return value;
    }
  }
  return "";
}

export default function WeatherAlertsList({ alerts }: WeatherAlertsListProps) {
  const rows = alerts?.length
    ? alerts.map((alert, index) => {
        const headline = getFirstString(alert, ["headline", "event", "title"]) || "Weather alert";
        const severity = getFirstString(alert, ["severity", "urgency", "category"]) || "unknown";
        const effective = getFirstString(alert, ["effective", "onset", "start"]) || "-";
        const expires = getFirstString(alert, ["expires", "end", "until"]) || "-";

        return (
          <tr key={`${headline}-${index}`}>
            <td>{headline}</td>
            <td>{severity}</td>
            <td>{effective}</td>
            <td>{expires}</td>
          </tr>
        );
      })
    : null;

  return (
    <Card title="Active Alerts">
      <Table headers={["Alert", "Severity", "Effective", "Expires"]} emptyMessage="No active alerts.">
        {rows}
      </Table>
    </Card>
  );
}
