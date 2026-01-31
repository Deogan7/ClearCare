import api from "./api";
import type {
  Referral,
  ReferralCreatePayload,
  ReferralUpdatePayload,
} from "../types/referral";

export async function getReferrals(status?: string) {
  if (status) {
    return api.get<Referral[]>(
      `/referrals/?status=${encodeURIComponent(status)}`
    );
  }
  return api.get<Referral[]>("/referrals/");
}

export async function getReferral(ticketId: string) {
  return api.get<Referral>(`/referrals/${ticketId}`);
}

export async function createReferral(data: ReferralCreatePayload) {
  return api.post<Referral>("/referrals/", data);
}

export async function updateReferral(
  ticketId: string,
  data: ReferralUpdatePayload
) {
  return api.patch<Referral>(`/referrals/${ticketId}`, data);
}
