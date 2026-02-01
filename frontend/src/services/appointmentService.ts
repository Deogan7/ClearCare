import api from "./api";
import type {
  Appointment,
  AppointmentCreatePayload,
  AppointmentUpdatePayload,
} from "../types/appointment";

export async function getAppointments(status?: string, riskLevel?: string) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (riskLevel) params.set("risk_level", riskLevel);
  const query = params.toString();
  return api.get<Appointment[]>(`/appointments/${query ? `?${query}` : ""}`);
}

export async function getAppointment(id: string) {
  return api.get<Appointment>(`/appointments/${id}`);
}

export async function createAppointment(data: AppointmentCreatePayload) {
  return api.post<Appointment>("/appointments/", data);
}

export async function updateAppointment(
  id: string,
  data: AppointmentUpdatePayload
) {
  return api.patch<Appointment>(`/appointments/${id}`, data);
}

export async function deleteAppointment(id: string) {
  return api.delete(`/appointments/${id}`);
}

export async function seedAppointments() {
  return api.post<Appointment[]>("/appointments/seed");
}
