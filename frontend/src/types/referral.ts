export type ReferralStatus =
  | "pending_confirmation"
  | "scheduled"
  | "attended"
  | "resolved"
  | "missed";

export interface Referral {
  id: string;
  ticket_id: string;
  patient_id: string;
  status: ReferralStatus;
  description: string | null;
  referred_to: string;
  action_date: string;
  scheduled_date: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ReferralCreatePayload {
  patient_id: string;
  description?: string | null;
  referred_to: string;
  specialist_phone?: string | null;
  action_date: string;
  scheduled_date?: string | null;
  notes?: string | null;
  created_by: string;
}

export interface ReferralUpdatePayload {
  status?: ReferralStatus;
  scheduled_date?: string | null;
  notes?: string | null;
}
