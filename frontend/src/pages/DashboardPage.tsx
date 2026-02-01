import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/common/AppShell";
import Button from "../components/common/Button";
import Card from "../components/common/Card";
import PageHeader from "../components/common/PageHeader";
import StatCard from "../components/common/StatCard";
import SideDrawer from "../components/common/SideDrawer";
import StormModeModal from "../components/storm/StormModeModal";
import { useStormMode } from "../context/StormModeContext";
import { getAppointments } from "../services/appointmentService";
import { getPatients } from "../services/patientService";
import { getReferrals } from "../services/referralService";
import { getStormStatus } from "../services/weatherService";
import type { Appointment } from "../types/appointment";
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
  taskType: string;
  context: string;
  dueLabel?: string;
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
  return status !== "closed" && status !== "missed";
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
  const {
    isActive: stormModeActive,
    status: stormModeStatus,
    wellnessSummary,
  } = useStormMode();
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [lastWeatherCheck, setLastWeatherCheck] = useState<Date | null>(null);
  const [isStormSevere, setIsStormSevere] = useState(false);
  const [stormStatus, setStormStatus] = useState<StormStatusResponse | null>(null);
  const [overdueOpen, setOverdueOpen] = useState(false);
  const [tasksOpen, setTasksOpen] = useState(false);
  const [stormModalOpen, setStormModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [referralsResult, patientsResult, stormResult, appointmentsResult] =
        await Promise.allSettled([
          getReferrals(),
          getPatients(),
          getStormStatus(),
          getAppointments(),
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
        const severe = Boolean(stormData?.is_severe);
        setIsStormSevere(severe);
        setStormStatus(stormData);
        setLastWeatherCheck(new Date());
      } else {
        setStormStatus(null);
      }

      if (appointmentsResult.status === "fulfilled") {
        setAppointments(
          Array.isArray(appointmentsResult.value.data)
            ? appointmentsResult.value.data
            : []
        );
      } else {
        setAppointments([]);
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

  const patientNameById = useMemo(() => {
    const map = new Map<string, string>();
    patients.forEach((patient) => {
      map.set(patient.id, `${patient.first_name} ${patient.last_name}`);
    });
    return map;
  }, [patients]);

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

  const todaysAppointments = useMemo(() => {
    return appointments.filter((a) => {
      const d = parseDate(a.appointment_date);
      if (!d) return false;
      return toDateOnly(d).getTime() === today.getTime();
    });
  }, [appointments, today]);

  const criticalAppointments = useMemo(() => {
    return appointments.filter(
      (a) =>
        a.risk_level === "critical" &&
        a.status !== "completed" &&
        a.status !== "cancelled"
    );
  }, [appointments]);

  const priorities = useMemo<PriorityItem[]>(() => {
    const items: PriorityItem[] = [];
    if (overdueReferrals.length > 0) {
      items.push({
        id: "overdue-referrals",
        label: `${overdueReferrals.length} overdue referrals need follow-up`,
        taskType: "Follow-up",
        context: "Overdue referrals",
        dueLabel: "Overdue",
      });
    }
    if (scheduledToday.length > 0) {
      items.push({
        id: "scheduled-today",
        label: `${scheduledToday.length} referrals scheduled for today`,
        taskType: "Confirm appointment",
        context: "Referrals scheduled today",
        dueLabel: "Today",
      });
    }
    if (highRiskPatients.length > 0) {
      items.push({
        id: "high-risk",
        label: `${highRiskPatients.length} high-risk patients need outreach`,
        taskType: "Outreach",
        context: "High-risk patients",
        dueLabel: "Today",
      });
    }
    if (criticalAppointments.length > 0) {
      items.push({
        id: "critical-appts",
        label: `${criticalAppointments.length} critical appointment(s) need attention`,
        taskType: "Review",
        context: "Critical risk appointments",
        dueLabel: "Urgent",
      });
    }
    return items;
  }, [criticalAppointments.length, highRiskPatients.length, overdueReferrals.length, scheduledToday.length]);

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
        action: () => setOverdueOpen(true),
        isSevere: true,
      };
    }
    if (alertState === "yellow") {
      return {
        title: "Attention needed",
        summary: `${overdueReferrals.length} overdue referrals require follow-up today.`,
        action: () => setOverdueOpen(true),
        isSevere: false,
      };
    }
    return {
      title: "All clear",
      summary: "No urgent items right now.",
      action: () => loadData(),
      isSevere: false,
    };
  }, [alertState, isStormSevere, loadData, overdueReferrals.length]);

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
      ? `${stormStatus.thresholds.temp_c}C / ${stormStatus.thresholds.snow_cm}cm`
      : "-- / --";
    return {
      temp: `${stormStatus.temperature_c}C`,
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
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <PageHeader
            title="Dashboard"
            subtitle="Today's referral load, storm risk, and outreach activity."
            actions={<Button onClick={() => navigate("/referrals")}>New Referral</Button>}
          />
          <div className="page-subtitle">{lastUpdatedLabel}</div>
        </div>

        {/* Storm Mode banner */}
        {stormModeActive && (
          <div className="storm-dashboard-banner">
            <div className="storm-banner-left">
              <span className="storm-banner-icon">{"\u26A1"}</span>
              <div className="storm-banner-info">
                <div className="storm-banner-title">Storm Mode Active</div>
                <div className="storm-banner-subtitle">
                  {stormModeStatus?.converted_count ?? 0} converted
                  {wellnessSummary
                    ? ` | ${wellnessSummary.completed}/${wellnessSummary.total} wellness checks`
                    : ""}
                  {stormModeStatus?.trigger === "auto" ? " (auto-triggered)" : ""}
                </div>
              </div>
            </div>
            <Button variant="ghost" onClick={() => setStormModalOpen(true)}>
              Manage
            </Button>
          </div>
        )}

        {/* Storm Wellness Triage Panel */}
        {stormModeActive && wellnessSummary && wellnessSummary.total > 0 && (
          <Card
            title="Storm Wellness Triage"
            action={
              <Button variant="ghost" onClick={() => setStormModalOpen(true)}>
                View all
              </Button>
            }
          >
            <div className="storm-triage-grid">
              <div className="storm-triage-stat">
                <div className="stat-number">{wellnessSummary.total}</div>
                <div className="stat-label">Patients Called</div>
              </div>
              <div className="storm-triage-stat">
                <div className="stat-number">{wellnessSummary.completed}</div>
                <div className="stat-label">Completed</div>
              </div>
              <div className="storm-triage-stat">
                <div className="stat-number text-danger">
                  {wellnessSummary.alerts.length}
                </div>
                <div className="stat-label">Need Attention</div>
              </div>
              <div className="storm-triage-stat">
                <div className="stat-number">
                  {wellnessSummary.checks.filter(
                    (c) => c.medication_stocked === false
                  ).length}
                </div>
                <div className="stat-label">Low on Meds</div>
              </div>
            </div>

            {wellnessSummary.alerts.length > 0 && (
              <div className="storm-triage-alerts">
                {wellnessSummary.alerts.slice(0, 3).map((alert) => (
                  <div key={alert.id} className="storm-triage-alert-row">
                    <span className="storm-triage-alert-name">
                      {alert.patient_name}
                    </span>
                    <div className="storm-triage-alert-badges">
                      {alert.has_symptoms && (
                        <span className="badge danger">Symptoms</span>
                      )}
                      {alert.medication_stocked === false && (
                        <span className="badge warn">Low Meds</span>
                      )}
                      {alert.needs_assistance && (
                        <span className="badge info">Needs Help</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {wellnessSummary.calling > 0 && (
              <div className="page-subtitle" style={{ marginTop: 8 }}>
                {wellnessSummary.calling} call(s) still in progress...
              </div>
            )}
          </Card>
        )}

        {/* Compact horizontal action strip for priorities */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            padding: "10px 12px",
            border: "1px solid var(--border)",
            borderRadius: 10,
            background: "var(--surface)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
            <strong>Today's priorities</strong>
            {priorities.length === 0 ? (
              <span className="page-subtitle">No urgent tasks today.</span>
            ) : (
              priorities.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setTasksOpen(true)}
                  className="button ghost"
                  style={{ padding: "4px 8px" }}
                >
                  {item.label}
                </button>
              ))
            )}
          </div>
          <button
            onClick={() => setTasksOpen(true)}
            className="button ghost"
            style={{ padding: "4px 8px" }}
          >
            View all &rarr;
          </button>
        </div>

        {/* Slim inline alert banner for attention state */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            padding: "8px 12px",
            borderLeft: `4px solid ${alertState === "red" ? "var(--danger)" : alertState === "yellow" ? "var(--warn)" : "var(--ok)"}`,
            background: "var(--surface)",
            borderRadius: 8,
          }}
        >
          <div>
            <strong>{alertContent.title}</strong>
            <div className="page-subtitle">{alertContent.summary}</div>
            <div className="page-subtitle">{lastWeatherLabel}</div>
          </div>
          <button
            onClick={alertContent.action}
            className="button ghost"
            style={{ padding: "4px 8px" }}
          >
            {alertState === "green" ? "Run check \u2192" : "View overdue \u2192"}
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 16,
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
            onClick={() => setOverdueOpen(true)}
          />
          <ClickableStatCard
            label="High-risk patients"
            value={`${highRiskPatients.length}`}
            helper="Storm contact list"
            onClick={() => navigate("/patients?highRisk=true")}
          />
          <ClickableStatCard
            label="Today's appts"
            value={`${todaysAppointments.length}`}
            helper={todaysAppointments.length > 0 ? "View schedule" : "No appointments today"}
            onClick={() => navigate("/appointments")}
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
              <div className="page-subtitle" style={{ padding: "6px 0" }}>
                No recent activity.
              </div>
            ) : (
              activityItems.map((item, index) => (
                <div
                  key={item.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px 0",
                    borderBottom: index === activityItems.length - 1 ? "none" : "1px solid var(--border)",
                  }}
                >
                  <span>{item.label}</span>
                  <span className="page-subtitle">{timeAgo(item.timestamp, new Date())}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
      <SideDrawer
        open={overdueOpen}
        title="Overdue referrals"
        onClose={() => setOverdueOpen(false)}
      >
        {/* Lightweight list keeps context visible behind the drawer */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {overdueReferrals.length === 0 ? (
            <div className="page-subtitle">No overdue referrals.</div>
          ) : (
            overdueReferrals.map((referral) => {
              const patientName =
                patientNameById.get(referral.patient_id) ?? "Unknown patient";
              const actionDate = parseDate(referral.action_date);
              const daysOverdue = actionDate
                ? Math.max(
                    0,
                    Math.floor(
                      (toDateOnly(new Date()).getTime() -
                        toDateOnly(actionDate).getTime()) /
                        86400000
                    )
                  )
                : 0;
              const reason = referral.status === "missed"
                ? "Missed appointment"
                : referral.scheduled_date
                ? "Follow-up overdue"
                : "Not scheduled";

              return (
                <div
                  key={referral.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 10,
                    padding: "10px 12px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{patientName}</div>
                  <div className="page-subtitle">Referral {referral.ticket_id}</div>
                  <div className="page-subtitle">
                    {reason} - {daysOverdue}d overdue
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="button secondary" style={{ padding: "6px 10px" }}>
                      Follow up
                    </button>
                    <button className="button ghost" style={{ padding: "6px 10px" }}>
                      Reschedule
                    </button>
                  </div>
                </div>
              );
            })
          )}
          <button
            className="button ghost"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/referrals")}
          >
            Open full referrals view &rarr;
          </button>
        </div>
      </SideDrawer>

      <SideDrawer
        open={tasksOpen}
        title="Today's tasks"
        onClose={() => setTasksOpen(false)}
      >
        {/* Tasks read as actions rather than raw referrals */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {priorities.length === 0 ? (
            <div className="page-subtitle">No tasks for today.</div>
          ) : (
            priorities.map((task) => (
              <div
                key={task.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                  padding: "10px 12px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>{task.taskType}</div>
                  <div className="page-subtitle">
                    {task.context} - {task.label}
                  </div>
                </div>
                <span className="badge warn">{task.dueLabel ?? "Today"}</span>
              </div>
            ))
          )}
          <button
            className="button ghost"
            style={{ alignSelf: "flex-start" }}
            onClick={() => navigate("/referrals")}
          >
            View all referrals &rarr;
          </button>
        </div>
      </SideDrawer>

      <StormModeModal open={stormModalOpen} onClose={() => setStormModalOpen(false)} />
    </AppShell>
  );
}
