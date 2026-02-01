import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "../../components/common/AppShell";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";
import PageHeader from "../../components/common/PageHeader";
import {
  getAppointments,
  updateAppointment,
  seedAppointments,
} from "../../services/appointmentService";
import { getPatients } from "../../services/patientService";
import type {
  Appointment,
  AppointmentStatus,
  RiskLevel,
} from "../../types/appointment";
import type { Patient } from "../../types/patient";
import AppointmentFormModal from "./AppointmentFormModal";

const RISK_CONFIG: Record<
  RiskLevel,
  { label: string; color: string; bg: string }
> = {
  critical: { label: "Critical", color: "#dc2626", bg: "rgba(220,38,38,0.1)" },
  high: { label: "High", color: "#ea580c", bg: "rgba(234,88,12,0.1)" },
  moderate: { label: "Moderate", color: "#d97706", bg: "rgba(217,119,6,0.1)" },
  low: { label: "Low", color: "#16a34a", bg: "rgba(22,163,74,0.1)" },
};

const STATUS_LABELS: Record<AppointmentStatus, string> = {
  scheduled: "Scheduled",
  confirmed: "Confirmed",
  checked_in: "Checked In",
  in_progress: "In Progress",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No Show",
};

const STATUS_BADGE: Record<AppointmentStatus, string> = {
  scheduled: "info",
  confirmed: "info",
  checked_in: "warn",
  in_progress: "warn",
  completed: "ok",
  cancelled: "danger",
  no_show: "danger",
};

type ViewMode = "timeline" | "table";

function formatDate(value: string) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function formatTime(value: string) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function isToday(value: string) {
  const d = new Date(value);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

function isPast(value: string) {
  const d = new Date(value);
  const now = new Date();
  return d < new Date(now.getFullYear(), now.getMonth(), now.getDate());
}

function RiskBadge({ level }: { level: RiskLevel }) {
  const cfg = RISK_CONFIG[level];
  return (
    <span
      className="appt-risk-badge"
      style={{
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}20`,
      }}
    >
      <span
        className="appt-risk-dot"
        style={{ background: cfg.color }}
      />
      {cfg.label}
    </span>
  );
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState<AppointmentStatus | "all">(
    "all"
  );
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "all">("all");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<ViewMode>("timeline");
  const [seeding, setSeeding] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [apptRes, patRes] = await Promise.all([
        getAppointments(),
        getPatients(),
      ]);
      setAppointments(Array.isArray(apptRes.data) ? apptRes.data : []);
      setPatients(Array.isArray(patRes.data) ? patRes.data : []);
    } catch {
      setError("Unable to load appointments.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const patientNameById = useMemo(() => {
    const map = new Map<string, string>();
    patients.forEach((p) =>
      map.set(p.id, `${p.first_name} ${p.last_name}`)
    );
    return map;
  }, [patients]);

  const filtered = useMemo(() => {
    const term = search.trim().toLowerCase();
    return appointments
      .filter((a) => {
        if (statusFilter !== "all" && a.status !== statusFilter) return false;
        if (riskFilter !== "all" && a.risk_level !== riskFilter) return false;
        if (term) {
          const patientName = patientNameById.get(a.patient_id) ?? "";
          const haystack =
            `${a.title} ${patientName} ${a.provider} ${a.description ?? ""}`.toLowerCase();
          if (!haystack.includes(term)) return false;
        }
        return true;
      })
      .sort(
        (a, b) =>
          new Date(a.appointment_date).getTime() -
          new Date(b.appointment_date).getTime()
      );
  }, [appointments, statusFilter, riskFilter, search, patientNameById]);

  // Group by date for timeline view
  const grouped = useMemo(() => {
    const groups = new Map<string, Appointment[]>();
    filtered.forEach((a) => {
      const key = formatDate(a.appointment_date);
      const arr = groups.get(key) ?? [];
      arr.push(a);
      groups.set(key, arr);
    });
    return groups;
  }, [filtered]);

  const stats = useMemo(() => {
    const today = appointments.filter((a) => isToday(a.appointment_date));
    const upcoming = appointments.filter(
      (a) =>
        !isPast(a.appointment_date) &&
        a.status !== "completed" &&
        a.status !== "cancelled"
    );
    const critical = appointments.filter(
      (a) =>
        a.risk_level === "critical" &&
        a.status !== "completed" &&
        a.status !== "cancelled"
    );
    const noShows = appointments.filter((a) => a.status === "no_show");
    return { today: today.length, upcoming: upcoming.length, critical: critical.length, noShows: noShows.length };
  }, [appointments]);

  const handleStatusChange = async (id: string, status: AppointmentStatus) => {
    try {
      await updateAppointment(id, { status });
      setAppointments((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status } : a))
      );
    } catch {
      // silently fail — user can retry
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedAppointments();
      await loadData();
    } catch {
      setError("Failed to seed appointments. They may already exist.");
    } finally {
      setSeeding(false);
    }
  };

  return (
    <AppShell>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <PageHeader
          title="Appointments"
          subtitle="Local appointment scheduling and management."
          actions={
            <div style={{ display: "flex", gap: 8 }}>
              {appointments.length === 0 && !loading && (
                <Button
                  variant="secondary"
                  onClick={handleSeed}
                  disabled={seeding}
                >
                  {seeding ? "Seeding..." : "Load Demo Data"}
                </Button>
              )}
              <Button onClick={() => setModalOpen(true)}>
                New Appointment
              </Button>
            </div>
          }
        />

        {/* Stats row */}
        <div className="appt-stats-row">
          <div className="appt-stat-chip">
            <span className="appt-stat-number">{stats.today}</span>
            <span className="appt-stat-label">Today</span>
          </div>
          <div className="appt-stat-chip">
            <span className="appt-stat-number">{stats.upcoming}</span>
            <span className="appt-stat-label">Upcoming</span>
          </div>
          <div className="appt-stat-chip appt-stat-critical">
            <span className="appt-stat-number">{stats.critical}</span>
            <span className="appt-stat-label">Critical</span>
          </div>
          <div className="appt-stat-chip appt-stat-noshow">
            <span className="appt-stat-number">{stats.noShows}</span>
            <span className="appt-stat-label">No-shows</span>
          </div>
        </div>

        {/* Filters */}
        <div className="filter-bar">
          <div className="filter-group">
            <span className="filter-label">Search</span>
            <input
              className="filter-search"
              type="text"
              placeholder="Patient, provider, title..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <span className="filter-label">Status</span>
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as AppointmentStatus | "all")
              }
            >
              <option value="all">All statuses</option>
              {(Object.keys(STATUS_LABELS) as AppointmentStatus[]).map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <span className="filter-label">Risk Level</span>
            <select
              className="filter-select"
              value={riskFilter}
              onChange={(e) =>
                setRiskFilter(e.target.value as RiskLevel | "all")
              }
            >
              <option value="all">All levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="moderate">Moderate</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="filter-group">
            <span className="filter-label">View</span>
            <div className="appt-view-toggle">
              <button
                className={`appt-view-btn ${view === "timeline" ? "active" : ""}`}
                onClick={() => setView("timeline")}
              >
                Timeline
              </button>
              <button
                className={`appt-view-btn ${view === "table" ? "active" : ""}`}
                onClick={() => setView("table")}
              >
                Table
              </button>
            </div>
          </div>
        </div>

        {loading && <div className="page-subtitle">Loading appointments...</div>}
        {error && <div className="form-error">{error}</div>}

        {!loading && !error && filtered.length === 0 && (
          <Card>
            <div style={{ textAlign: "center", padding: "32px 0" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
              <strong>No appointments found</strong>
              <div className="page-subtitle" style={{ marginTop: 4 }}>
                {appointments.length === 0
                  ? "Click \"Load Demo Data\" or create your first appointment."
                  : "Try adjusting your filters."}
              </div>
            </div>
          </Card>
        )}

        {/* Timeline view */}
        {!loading && !error && filtered.length > 0 && view === "timeline" && (
          <div className="appt-timeline">
            {Array.from(grouped.entries()).map(([dateLabel, appts]) => {
              const dayIsToday = appts[0]
                ? isToday(appts[0].appointment_date)
                : false;
              const dayIsPast = appts[0]
                ? isPast(appts[0].appointment_date)
                : false;
              return (
                <div key={dateLabel} className="appt-day-group">
                  <div className="appt-day-header">
                    <span className={`appt-day-label ${dayIsToday ? "today" : dayIsPast ? "past" : ""}`}>
                      {dayIsToday ? `Today — ${dateLabel}` : dateLabel}
                    </span>
                    <span className="appt-day-count">
                      {appts.length} appointment{appts.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="appt-day-cards">
                    {appts.map((appt) => (
                      <div
                        key={appt.id}
                        className={`appt-card ${appt.status === "completed" || appt.status === "cancelled" ? "dimmed" : ""}`}
                      >
                        <div className="appt-card-left">
                          <div
                            className="appt-card-time-strip"
                            style={{
                              borderColor: RISK_CONFIG[appt.risk_level].color,
                            }}
                          >
                            <span className="appt-card-time">
                              {formatTime(appt.appointment_date)}
                            </span>
                            <span className="appt-card-duration">
                              {appt.duration_minutes}m
                            </span>
                          </div>
                        </div>
                        <div className="appt-card-body">
                          <div className="appt-card-top">
                            <strong>{appt.title}</strong>
                            <RiskBadge level={appt.risk_level} />
                          </div>
                          <div className="appt-card-meta">
                            <span>
                              {patientNameById.get(appt.patient_id) ?? "Unknown"}
                            </span>
                            <span className="appt-card-sep" />
                            <span>{appt.provider}</span>
                            {appt.location && (
                              <>
                                <span className="appt-card-sep" />
                                <span>{appt.location}</span>
                              </>
                            )}
                          </div>
                          {appt.description && (
                            <div className="appt-card-desc">
                              {appt.description}
                            </div>
                          )}
                        </div>
                        <div className="appt-card-right">
                          <span className={`badge ${STATUS_BADGE[appt.status]}`}>
                            {STATUS_LABELS[appt.status]}
                          </span>
                          {appt.status === "scheduled" && (
                            <button
                              className="button secondary appt-action-btn"
                              onClick={() =>
                                handleStatusChange(appt.id, "confirmed")
                              }
                            >
                              Confirm
                            </button>
                          )}
                          {appt.status === "confirmed" && (
                            <button
                              className="button secondary appt-action-btn"
                              onClick={() =>
                                handleStatusChange(appt.id, "checked_in")
                              }
                            >
                              Check In
                            </button>
                          )}
                          {appt.status === "checked_in" && (
                            <button
                              className="button secondary appt-action-btn"
                              onClick={() =>
                                handleStatusChange(appt.id, "in_progress")
                              }
                            >
                              Start
                            </button>
                          )}
                          {appt.status === "in_progress" && (
                            <button
                              className="button primary appt-action-btn"
                              onClick={() =>
                                handleStatusChange(appt.id, "completed")
                              }
                            >
                              Complete
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Table view */}
        {!loading && !error && filtered.length > 0 && view === "table" && (
          <Card>
            <div style={{ overflowX: "auto" }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Title</th>
                    <th>Patient</th>
                    <th>Provider</th>
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Location</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((appt) => (
                    <tr key={appt.id}>
                      <td>
                        <div style={{ whiteSpace: "nowrap" }}>
                          {formatDate(appt.appointment_date)}
                        </div>
                        <div
                          className="page-subtitle"
                          style={{ marginTop: 0 }}
                        >
                          {formatTime(appt.appointment_date)}
                        </div>
                      </td>
                      <td>
                        <strong>{appt.title}</strong>
                        {appt.description && (
                          <div
                            className="page-subtitle"
                            style={{
                              marginTop: 2,
                              maxWidth: 240,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {appt.description}
                          </div>
                        )}
                      </td>
                      <td>
                        {patientNameById.get(appt.patient_id) ?? "Unknown"}
                      </td>
                      <td>{appt.provider}</td>
                      <td>
                        <RiskBadge level={appt.risk_level} />
                      </td>
                      <td>
                        <span className={`badge ${STATUS_BADGE[appt.status]}`}>
                          {STATUS_LABELS[appt.status]}
                        </span>
                      </td>
                      <td>{appt.location ?? "—"}</td>
                      <td>{appt.duration_minutes}m</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>

      <AppointmentFormModal
        open={modalOpen}
        patients={patients}
        onClose={() => setModalOpen(false)}
        onCreated={loadData}
      />
    </AppShell>
  );
}
