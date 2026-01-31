# Member 4 — What Was Done

## Part 4: Data Privacy & Security Hardening

### New Files
- `backend/app/core/middleware.py` — HTTPS redirect middleware (active when `DEBUG=False`)
- `docs/PRIVACY_AUDIT.md` — audit of API responses and logs for sensitive data

### Modified Files
- `backend/app/main.py` — added `SecurityHeadersMiddleware` and `HTTPSRedirectMiddleware`

### Security Headers Added
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Privacy Audit Findings
- `PatientResponse` exposes all fields — acceptable since access is JWT-protected for nurses
- `hashed_password` is never returned — no User response schema exists
- Phone numbers logged in `voice_service.py` and `sms_service.py` — flagged for production masking
- No patient PII in route handler logs

### Production Notes
- Set `DEBUG=False` to activate HTTPS redirect
- Add `?ssl=require` to `DATABASE_URL` for encrypted DB connections
- Use cloud disk encryption (EBS/Azure) for at-rest protection
