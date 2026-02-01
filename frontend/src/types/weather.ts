export type WeatherThresholds = {
  snow_cm: number;
  temp_c: number;
};

export type WeatherLocation = {
  lat: number;
  lon: number;
};

export type CurrentWeatherResponse = {
  temperature_c: number;
  snow_cm: number;
  description: string;
  is_severe: boolean;
  thresholds: WeatherThresholds;
  location: WeatherLocation;
};

export type WeatherAlert = Record<string, unknown>;

export type StormStatusResponse = {
  is_severe: boolean;
  temperature_c: number;
  snow_cm: number;
  description: string;
  thresholds: WeatherThresholds;
  alerts: WeatherAlert[];
};

export type StormModeStatus = {
  is_active: boolean;
  trigger: string | null;
  activated_at: string | null;
  window_hours: number | null;
  converted_count: number;
  activated_by: string | null;
  event_id: string | null;
};

export type StormModeActivateResponse = {
  status: string;
  trigger: string | null;
  window_hours: number | null;
  converted_count: number;
  activated_at: string | null;
};

export type ConvertiblePreview = {
  count: number;
  window_hours: number;
};

// Storm Wellness Check types

export type WellnessCheckStatus = "pending" | "calling" | "completed" | "failed" | "skipped";

export type WellnessCheckItem = {
  id: string;
  patient_id: string;
  patient_name: string;
  status: WellnessCheckStatus;
  feeling_ok: boolean | null;
  has_symptoms: boolean | null;
  symptom_details: string | null;
  medication_stocked: boolean | null;
  needs_assistance: boolean | null;
  assistance_details: string | null;
  called_at: string | null;
  completed_at: string | null;
};

export type WellnessCheckSummary = {
  total: number;
  pending: number;
  calling: number;
  completed: number;
  failed: number;
  skipped: number;
  checks: WellnessCheckItem[];
  alerts: WellnessCheckItem[];
};

// Driver Notification types

export type DriverNotificationItem = {
  id: string;
  ticket_id: string;
  driver_name: string | null;
  patient_name: string;
  message: string;
  status: string;
  created_at: string;
};

export type DriverNotificationSummary = {
  total: number;
  notifications: DriverNotificationItem[];
};
