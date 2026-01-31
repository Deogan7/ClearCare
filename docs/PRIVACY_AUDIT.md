# Privacy Audit

Audit of API responses and server logs for sensitive data exposure.

---

## Response Schemas

### PatientResponse
- Exposes: `first_name`, `last_name`, `phone`, `address`, `notes`, `date_of_birth`
- All fields are needed by nurses operating the dashboard, so this is acceptable for authenticated users behind JWT
- `phone` could be masked in a future list endpoint if broader access roles are added

### ReferralResponse
- Exposes: `description`, `notes`, `referred_to`, `patient_id`
- No direct patient PII — references patient by UUID only
- Notes may contain voice-call summaries but are only visible to authenticated staff

### TokenResponse
- Returns `access_token` and `token_type` only
- `hashed_password` is never serialized — the User model has no response schema

---

## Server Logs

### voice_service.py
- Logs `admin_phone` when initiating verification calls — should be masked in production
- Patient references use `ticket_id` and `patient.id` (UUID) only — safe

### sms_service.py
- Logs the `to` phone number when sending SMS — should be masked in production

### Route handlers
- No `print()` or `logger` calls that output patient names, addresses, or notes

---

## Decisions

| Item | Decision |
|------|----------|
| PatientResponse fields | Keep all fields — nurses need full info; access is JWT-protected |
| Phone masking | Not implemented now; revisit if non-nurse roles are added |
| hashed_password exposure | Not possible — no User response schema exists |
| Log PII (phone numbers) | Flagged for production hardening; acceptable in dev |
| Database encryption at rest | Use `?ssl=require` on DATABASE_URL in production; rely on cloud disk encryption (EBS/Azure) for at-rest |

---

## Security Hardening Applied

- HTTPS redirect middleware (`HTTPSRedirectMiddleware`) — active when `DEBUG=False`
- Security headers middleware — `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`
- All API endpoints (except `/health`, `/api/auth/login`, `/api/voice/webhook`) require JWT Bearer token
