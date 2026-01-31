import api from "./api";
import type {
  Patient,
  PatientCreatePayload,
  PatientUpdatePayload,
} from "../types/patient";

export async function getPatients() {
  return api.get<Patient[]>("/patients/");
}

export async function getPatient(id: string) {
  return api.get<Patient>(`/patients/${id}`);
}

export async function createPatient(data: PatientCreatePayload) {
  return api.post<Patient>("/patients/", data);
}

export async function updatePatient(id: string, data: PatientUpdatePayload) {
  return api.patch<Patient>(`/patients/${id}`, data);
}
