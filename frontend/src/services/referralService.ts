import api from "./api";

export async function getReferrals() {
  return api.get("/referrals");
}

export async function createReferral(data: Record<string, unknown>) {
  return api.post("/referrals", data);
}

export async function updateReferral(
  ticketId: string,
  data: Record<string, unknown>
) {
  return api.patch(`/referrals/${ticketId}`, data);
}
