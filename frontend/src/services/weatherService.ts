import api from "./api";
import type { CurrentWeatherResponse, StormStatusResponse } from "../types/weather";

export async function getStormStatus(): Promise<StormStatusResponse> {
  const response = await api.get<StormStatusResponse>("/weather/storm-status");
  return response.data;
}

export async function getCurrentWeather(): Promise<CurrentWeatherResponse> {
  const response = await api.get<CurrentWeatherResponse>("/weather/current");
  return response.data;
}
