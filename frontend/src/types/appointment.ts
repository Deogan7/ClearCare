export type RiskLevel = "low" | "moderate" | "high" | "critical";

export type AppointmentStatus =
  | "scheduled"
  | "confirmed"
  | "checked_in"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "no_show";

export interface Appointment {
  id: string;
  patient_id: string;
  title: string;
  description: string | null;
  risk_level: RiskLevel;
  appointment_date: string;
  duration_minutes: number;
  provider: string;
  status: AppointmentStatus;
  location: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppointmentCreatePayload {
  patient_id: string;
  title: string;
  description?: string | null;
  risk_level?: RiskLevel;
  appointment_date: string;
  duration_minutes?: number;
  provider: string;
  location?: string | null;
  notes?: string | null;
}

export interface AppointmentUpdatePayload {
  title?: string | null;
  description?: string | null;
  risk_level?: RiskLevel | null;
  appointment_date?: string | null;
  duration_minutes?: number | null;
  provider?: string | null;
  status?: AppointmentStatus | null;
  location?: string | null;
  notes?: string | null;
}
