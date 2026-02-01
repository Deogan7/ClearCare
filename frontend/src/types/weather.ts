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
