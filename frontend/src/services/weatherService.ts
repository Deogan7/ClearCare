import api from "./api";

export async function getStormStatus() {
  return api.get("/weather/storm-status");
}

export async function getCurrentWeather() {
  return api.get("/weather/current");
}
