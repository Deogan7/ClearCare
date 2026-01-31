export interface Patient {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  date_of_birth: string | null;
  is_high_risk: boolean;
  address: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface PatientCreatePayload {
  first_name: string;
  last_name: string;
  phone: string;
  date_of_birth?: string | null;
  is_high_risk?: boolean;
  address?: string | null;
  notes?: string | null;
}

export interface PatientUpdatePayload {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  date_of_birth?: string | null;
  is_high_risk?: boolean | null;
  address?: string | null;
  notes?: string | null;
}
