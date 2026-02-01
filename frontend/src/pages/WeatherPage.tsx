import { useCallback, useEffect, useState } from "react";
import AppShell from "../components/common/AppShell";
import Button from "../components/common/Button";
import ErrorState from "../components/common/ErrorState";
import PageHeader from "../components/common/PageHeader";
import Skeleton from "../components/common/Skeleton";
import CurrentWeatherCard from "../components/weather/CurrentWeatherCard";
import StormStatusCard from "../components/weather/StormStatusCard";
import WeatherAlertsList from "../components/weather/WeatherAlertsList";
import { getCurrentWeather, getStormStatus } from "../services/weatherService";
import type { CurrentWeatherResponse, StormStatusResponse } from "../types/weather";

export default function WeatherPage() {
  const [current, setCurrent] = useState<CurrentWeatherResponse | null>(null);
  const [status, setStatus] = useState<StormStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadWeather = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [currentResponse, statusResponse] = await Promise.all([
        getCurrentWeather(),
        getStormStatus(),
      ]);
      setCurrent(currentResponse);
      setStatus(statusResponse);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load weather data", err);
      setError("Unable to load weather data right now.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadWeather();
  }, [loadWeather]);

  return (
    <AppShell>
      <div>
        <PageHeader
          title="Weather"
          subtitle="Monitor Storm Mode thresholds and alerts."
          actions={
            <Button variant="secondary" onClick={loadWeather} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
          }
        />
        {lastUpdated ? (
          <div className="page-subtitle">Last updated: {lastUpdated.toLocaleString()}</div>
        ) : null}
        {error ? <ErrorState message={error} /> : null}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 16,
          }}
        >
          {loading ? (
            <>
              <div className="card">
                <div className="card-header">
                  <strong>Current Conditions</strong>
                </div>
                <Skeleton height="32px" />
                <Skeleton />
                <Skeleton width="60%" />
              </div>
              <div className="card">
                <div className="card-header">
                  <strong>Storm Status</strong>
                </div>
                <Skeleton height="32px" />
                <Skeleton />
                <Skeleton width="60%" />
              </div>
            </>
          ) : (
            <>
              {current ? <CurrentWeatherCard data={current} /> : null}
              {status ? <StormStatusCard data={status} /> : null}
            </>
          )}
        </div>
        {!loading && status ? <WeatherAlertsList alerts={status.alerts ?? []} /> : null}
      </div>
    </AppShell>
  );
}
