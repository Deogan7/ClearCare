import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/common/AppShell";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import { getPatients } from "../services/patientService";
import { getReferrals } from "../services/referralService";
import { getStormStatus } from "../services/weatherService";
import type { Patient } from "../types/patient";
import type { Referral } from "../types/referral";
import type { StormStatusResponse } from "../types/weather";

interface ActivityItem {
  id: string;
  label: string;
  timestamp: Date;
}

interface PriorityItem {
  id: string;
  label: string;
  onClick: () => void;
}

function formatTime(value: Date) {
  return value.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function timeAgo(from: Date, to: Date) {
  const diffMs = Math.max(0, to.getTime() - from.getTime());
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) {
    return "just now";
  }
  if (minutes < 60) {
    return `${minutes} min ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hr ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function toDateOnly(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function parseDate(value?: string | null) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function isActiveReferral(status: Referral["status"]) {
  return status !== "resolved" && status !== "missed";
}

function ClickableStatCard({
  label,
  value,
  helper,
  onClick,
}: {
  label: string;
  value: string;
  helper?: string;
  onClick: () => void;
}) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      style={{ cursor: "pointer" }}
    >
      <StatCard label={label} value={value} helper={helper} />
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [lastWeatherCheck, setLastWeatherCheck] = useState<Date | null>(null);
  const [isStormSevere, setIsStormSevere] = useState(false);
  const [stormStatus, setStormStatus] = useState<StormStatusResponse | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [referralsResult, patientsResult, stormResult] =
        await Promise.allSettled([
          getReferrals(),
          getPatients(),
          getStormStatus(),
        ]);

      if (referralsResult.status === "fulfilled") {
        setReferrals(
          Array.isArray(referralsResult.value.data)
            ? referralsResult.value.data
            : []
        );
      } else {
        setReferrals([]);
      }

      if (patientsResult.status === "fulfilled") {
        setPatients(
          Array.isArray(patientsResult.value.data)
            ? patientsResult.value.data
            : []
        );
      } else {
        setPatients([]);
      }

      if (stormResult.status === "fulfilled") {
        const stormData = stormResult.value ?? null;
        const severe = Boolean(
          stormData?.is_severe ?? stormData?.isSevere ?? stormData?.severe
        );
        setIsStormSevere(severe);
        setStormStatus(stormData);
        setLastWeatherCheck(new Date());
      } else {
        setStormStatus(null);
      }

      setLastUpdated(new Date());
    } catch {
      setLastUpdated(new Date());
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const today = useMemo(() => toDateOnly(new Date()), []);

  const overdueReferrals = useMemo(() => {
    return referrals.filter((referral) => {
      const actionDate = parseDate(referral.action_date);
      if (!actionDate) {
        return false;
      }
      const isOverdue = actionDate < today;
      return isOverdue && isActiveReferral(referral.status);
    });
  }, [referrals, today]);

  const scheduledToday = useMemo(() => {
    return referrals.filter((referral) => {
      const scheduledDate = parseDate(referral.scheduled_date);
      if (!scheduledDate) {
        return false;
      }
      return toDateOnly(scheduledDate).getTime() === today.getTime();
    });
  }, [referrals, today]);

  const highRiskPatients = useMemo(() => {
    return patients.filter((patient) => patient.is_high_risk);
  }, [patients]);

  const activeReferrals = useMemo(() => {
    return referrals.filter((referral) => isActiveReferral(referral.status));
  }, [referrals]);

  const priorities = useMemo<PriorityItem[]>(() => {
    const items: PriorityItem[] = [];
    if (overdueReferrals.length > 0) {
      items.push({
        id: "overdue-referrals",
        label: `${overdueReferrals.length} overdue referrals need follow-up`,
        onClick: () => navigate("/referrals?overdue=true"),
      });
    }
    if (scheduledToday.length > 0) {
      items.push({
        id: "scheduled-today",
        label: `${scheduledToday.length} referrals scheduled for today`,
        onClick: () => navigate("/referrals?status=scheduled&date=today"),
      });
    }
    if (highRiskPatients.length > 0) {
      items.push({
        id: "high-risk",
        label: `${highRiskPatients.length} high-risk patients need outreach`,
        onClick: () => navigate("/patients?highRisk=true"),
      });
    }
    return items;
  }, [highRiskPatients.length, navigate, overdueReferrals.length, scheduledToday.length]);

  const alertState = useMemo(() => {
    if (isStormSevere || overdueReferrals.length > 1) {
      return "red";
    }
    if (overdueReferrals.length > 0) {
      return "yellow";
    }
    return "green";
  }, [isStormSevere, overdueReferrals.length]);

  const alertContent = useMemo(() => {
    if (alertState === "red") {
      return {
        title: "Action required",
        summary: isStormSevere
          ? "Severe weather conditions detected. Prioritize outreach."
          : "Multiple overdue referrals need immediate attention.",
        actionLabel: "Review outreach",
        action: () => navigate("/referrals?overdue=true"),
        isSevere: true,
      };
    }
    if (alertState === "yellow") {
      return {
        title: "Attention needed",
        summary: `${overdueReferrals.length} overdue referrals require follow-up today.`,
        actionLabel: "View overdue",
        action: () => navigate("/referrals?overdue=true"),
        isSevere: false,
      };
    }
    return {
      title: "All clear",
      summary: "No urgent items right now.",
      actionLabel: "Trigger weather check",
      action: () => loadData(),
      isSevere: false,
    };
  }, [alertState, isStormSevere, loadData, navigate, overdueReferrals.length]);

  const activityItems = useMemo<ActivityItem[]>(() => {
    const items: ActivityItem[] = [];

    referrals.forEach((referral) => {
      const createdAt = parseDate(referral.created_at);
      if (createdAt) {
        items.push({
          id: `referral-created-${referral.id}`,
          label: `Referral ${referral.ticket_id} created`,
          timestamp: createdAt,
        });
      }
      const updatedAt = parseDate(referral.updated_at);
      if (updatedAt && createdAt && updatedAt.getTime() !== createdAt.getTime()) {
        items.push({
          id: `referral-updated-${referral.id}`,
          label: `Referral ${referral.ticket_id} status updated`,
          timestamp: updatedAt,
        });
      }
    });

    patients.forEach((patient) => {
      const createdAt = parseDate(patient.created_at);
      if (createdAt) {
        items.push({
          id: `patient-created-${patient.id}`,
          label: `Patient ${patient.first_name} ${patient.last_name} created`,
          timestamp: createdAt,
        });
      }
    });

    if (lastWeatherCheck) {
      items.push({
        id: "weather-check",
        label: "Weather check triggered",
        timestamp: lastWeatherCheck,
      });
    }

    return items
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
      .slice(0, 5);
  }, [lastWeatherCheck, patients, referrals]);

  const lastUpdatedLabel = useMemo(() => {
    if (!lastUpdated) {
      return "Last updated: --";
    }
    return `Last updated: ${timeAgo(lastUpdated, new Date())}`;
  }, [lastUpdated]);

  const lastWeatherLabel = useMemo(() => {
    if (!lastWeatherCheck) {
      return "Last weather check: --";
    }
    return `Last weather check: ${formatTime(lastWeatherCheck)}`;
  }, [lastWeatherCheck]);

  const weatherSummary = useMemo(() => {
    if (!stormStatus) {
      return {
        temp: "--",
        snow: "--",
        description: "Weather data unavailable.",
        alerts: 0,
        thresholds: "-- / --",
        severityClass: "info",
        severityLabel: "unknown",
      };
    }
    const thresholds = stormStatus.thresholds
      ? `${stormStatus.thresholds.temp_c}°C / ${stormStatus.thresholds.snow_cm}cm`
      : "-- / --";
    return {
      temp: `${stormStatus.temperature_c}°C`,
      snow: `${stormStatus.snow_cm}cm`,
      description: stormStatus.description || "No description available.",
      alerts: Array.isArray(stormStatus.alerts) ? stormStatus.alerts.length : 0,
      thresholds,
      severityClass: stormStatus.is_severe ? "danger" : "ok",
      severityLabel: stormStatus.is_severe ? "severe" : "clear",
    };
  }, [stormStatus]);

  return (
    <AppShell>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <PageHeader
            title="Dashboard"
            subtitle="Today's referral load, storm risk, and outreach activity."
            actions={<Button onClick={() => navigate("/referrals")}>New Referral</Button>}
          />
          <div className="page-subtitle">{lastUpdatedLabel}</div>
        </div>

        <Card title="Today's priorities">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {priorities.length === 0 ? (
              <div className="page-subtitle">No urgent tasks today.</div>
            ) : (
              priorities.map((item) => (
                <Button
                  key={item.id}
                  variant="secondary"
                  onClick={item.onClick}
                >
                  {item.label}
                </Button>
              ))
            )}
          </div>
        </Card>

        <div className={`storm-banner ${alertContent.isSevere ? "severe" : "safe"}`}>
          <div>
            <strong>{alertContent.title}</strong>
            <div className="page-subtitle">{alertContent.summary}</div>
            <div className="page-subtitle">{lastWeatherLabel}</div>
          </div>
          <Button
            variant={alertContent.isSevere ? "danger" : "secondary"}
            onClick={alertContent.action}
          >
            {alertContent.actionLabel}
          </Button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 20,
          }}
        >
          <ClickableStatCard
            label="Active referrals"
            value={`${activeReferrals.length}`}
            helper="View all open cases"
            onClick={() => navigate("/referrals?status=active")}
          />
          <ClickableStatCard
            label="Overdue follow-ups"
            value={`${overdueReferrals.length}`}
            helper="Needs review"
            onClick={() => navigate("/referrals?overdue=true")}
          />
          <ClickableStatCard
            label="High-risk patients"
            value={`${highRiskPatients.length}`}
            helper="Storm contact list"
            onClick={() => navigate("/patients?highRisk=true")}
          />
          <ClickableStatCard
            label="Weather alerts"
            value={`${weatherSummary.alerts}`}
            helper={weatherSummary.alerts > 0 ? "Review active alerts" : "No warnings"}
            onClick={() => navigate("/weather")}
          />
        </div>

        <Card
          title="Weather snapshot"
          action={<span className={`badge ${weatherSummary.severityClass}`}>{weatherSummary.severityLabel}</span>}
        >
          <div className="page-subtitle">{weatherSummary.description}</div>
          <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
            <div>
              <strong>{weatherSummary.temp}</strong>
              <div className="page-subtitle">Temperature</div>
            </div>
            <div>
              <strong>{weatherSummary.snow}</strong>
              <div className="page-subtitle">Snowfall</div>
            </div>
            <div>
              <strong>{weatherSummary.alerts}</strong>
              <div className="page-subtitle">Active alerts</div>
            </div>
            <div>
              <strong>{weatherSummary.thresholds}</strong>
              <div className="page-subtitle">Thresholds</div>
            </div>
          </div>
        </Card>

        <Card title="Recent activity">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {activityItems.length === 0 ? (
              <div className="page-subtitle">No recent activity.</div>
            ) : (
              activityItems.map((item) => (
                <div key={item.id} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{item.label}</span>
                  <span className="page-subtitle">{timeAgo(item.timestamp, new Date())}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
