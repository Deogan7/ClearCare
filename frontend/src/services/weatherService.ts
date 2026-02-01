import api from "./api";
import type {
  CurrentWeatherResponse,
  StormStatusResponse,
  StormModeStatus,
  StormModeActivateResponse,
  ConvertiblePreview,
} from "../types/weather";

export async function getStormStatus(): Promise<StormStatusResponse> {
  const response = await api.get<StormStatusResponse>("/weather/storm-status");
  return response.data;
}

export async function getCurrentWeather(): Promise<CurrentWeatherResponse> {
  const response = await api.get<CurrentWeatherResponse>("/weather/current");
  return response.data;
}

export async function getStormModeStatus(): Promise<StormModeStatus> {
  const response = await api.get<StormModeStatus>("/storm-mode/status");
  return response.data;
}

export async function activateStormMode(
  mode: "manual" | "auto" = "manual",
  windowHours = 48
): Promise<StormModeActivateResponse> {
  const response = await api.post<StormModeActivateResponse>("/storm-mode/activate", {
    mode,
    window_hours: windowHours,
  });
  return response.data;
}

export async function deactivateStormMode(): Promise<StormModeActivateResponse> {
  const response = await api.post<StormModeActivateResponse>("/storm-mode/deactivate");
  return response.data;
}

export async function previewConversions(windowHours = 48): Promise<ConvertiblePreview> {
  const response = await api.get<ConvertiblePreview>("/storm-mode/preview", {
    params: { window_hours: windowHours },
  });
  return response.data;
}
