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
