# RidgeCare Link — Next Steps

This document outlines the remaining work required to bring RidgeCare Link from its current scaffolding state to a functional application, based on the PRD and TRD defined in `CLAUDE.md`.

---

## Current State

The project has a fully scaffolded structure with:

- **Backend**: FastAPI app with models, schemas, services, and background tasks defined — but all API route handlers are empty stubs (`pass`). Services (referral, weather, SMS, voice) have real logic. Security, shared dependencies, Alembic migrations, and tests are empty placeholders.
- **Frontend**: Vite + React + Tailwind CSS with routing to four pages and API service wrappers — but all page components render placeholder text with no UI or data fetching.

---

## Phase 1: Backend API Implementation

The service layer is already written. The routes need to be wired up to call those services.

### 1.1 Patient Endpoints (`backend/app/api/routes/patients.py`)

- [ ] `GET /api/patients/` — Query all patients from the database, return as `PatientResponse` list
- [ ] `POST /api/patients/` — Validate `PatientCreate` payload, insert into database, return created patient
- [ ] `GET /api/patients/{patient_id}` — Look up patient by UUID, return 404 if not found

### 1.2 Referral Endpoints (`backend/app/api/routes/referrals.py`)

- [ ] `GET /api/referrals/` — Query referrals (consider filtering by status), return as `ReferralResponse` list
- [ ] `POST /api/referrals/` — Call `referral_service.create_referral()`, return created referral with ticket ID
- [ ] `GET /api/referrals/{ticket_id}` — Call `referral_service.get_referral_by_ticket_id()`, return 404 if not found
- [ ] `PATCH /api/referrals/{ticket_id}` — Call `referral_service.update_referral()`, handle `ValueError` for invalid state transitions (return 422)

### 1.3 Weather Endpoints (`backend/app/api/routes/weather.py`)

- [ ] `GET /api/weather/current` — Call `weather_service.fetch_current_weather()`, return weather condition data
- [ ] `GET /api/weather/storm-status` — Fetch weather and return whether storm mode thresholds are exceeded, along with current readings

### 1.4 Voice Endpoints (`backend/app/api/routes/voice.py`)

- [ ] `POST /api/voice/verify-referral/{ticket_id}` — Look up referral, call `voice_service.verify_referral_receipt()`, return call status
- [ ] `POST /api/voice/patient-checkin/{patient_id}` — Look up patient and active referrals, call `voice_service.initiate_patient_follow_up_call()`
- [ ] `POST /api/voice/webhook` — Parse Vapi webhook payload, update referral notes/status based on call transcription results

---

## Phase 2: Database & Migrations

### 2.1 Alembic Configuration (`backend/alembic/env.py`)

- [ ] Configure async engine in the Alembic environment file
- [ ] Import `Base.metadata` from models so Alembic can detect schema changes
- [ ] Generate the initial migration from current models (`alembic revision --autogenerate`)
- [ ] Verify migration runs cleanly against a fresh PostgreSQL database

### 2.2 Database Seeding

- [ ] Create a seed script or management command to populate test patients and referrals for development

---

## Phase 3: Security & Auth (`backend/app/core/security.py`, `backend/app/api/deps.py`)

### 3.1 Authentication

- [ ] Decide on auth strategy (JWT tokens, session-based, or API keys — the TRD does not prescribe one)
- [ ] Implement login endpoint or API key validation
- [ ] Create a `get_current_user` dependency in `deps.py` for protecting routes

### 3.2 Authorization

- [ ] Define role-based access (nurse vs. admin) if needed for the dashboard
- [ ] Apply auth dependencies to route handlers

### 3.3 Data Privacy

- [ ] Ensure patient data encryption at rest (database-level or field-level)
- [ ] Add HTTPS enforcement for production
- [ ] Audit for sensitive data exposure in API responses

---

## Phase 4: Frontend Implementation

### 4.1 Shared Components

- [ ] Create a layout shell with navigation sidebar/header linking to Dashboard, Referrals, Patients, Weather
- [ ] Build reusable table component for listing data
- [ ] Build reusable form components (inputs, selects, date pickers)
- [ ] Add loading states and error handling for API calls
- [ ] Add toast/notification system for success and error feedback

### 4.2 Dashboard Page (`frontend/src/pages/DashboardPage.tsx`)

- [ ] Summary cards: total active referrals, overdue referrals, high-risk patients count
- [ ] Storm Mode status banner (green/red indicator with current weather)
- [ ] Recent activity feed showing latest referral state changes
- [ ] Quick-action buttons (create referral, trigger weather check)

### 4.3 Referrals Page (`frontend/src/pages/ReferralsPage.tsx`)

- [ ] Referral list table with columns: ticket ID, patient name, status, referred to, scheduled date, action date
- [ ] Status filter (Pending, Scheduled, Attended, Resolved, Missed)
- [ ] Create referral form/modal (patient selection, description, referred to, dates)
- [ ] Referral detail view with status timeline and update form
- [ ] Status transition buttons with validation (only show valid next states)

### 4.4 Patients Page (`frontend/src/pages/PatientsPage.tsx`)

- [ ] Patient list table with columns: name, phone, high-risk flag, number of active referrals
- [ ] Create/edit patient form (name, phone, DOB, address, high-risk toggle, notes)
- [ ] Patient detail view showing their referral history
- [ ] Add a `patientService.ts` API wrapper (currently missing)

### 4.5 Weather Page (`frontend/src/pages/WeatherPage.tsx`)

- [ ] Current weather conditions display (temperature, snowfall, description)
- [ ] Storm Mode status with threshold indicators (snow >= 15cm, temp <= -35°C)
- [ ] Active weather alerts list
- [ ] Manual "Activate Storm Mode" override button for nurses
- [ ] Log of recent storm mode activations and actions taken

---

## Phase 5: Vapi Webhook & NLP Processing

The TRD requires transcription analysis and automatic ticket updates from voice call results.

- [ ] Define the Vapi webhook payload schema (based on Vapi API documentation)
- [ ] Implement webhook handler to parse call status (completed, failed, no-answer)
- [ ] Extract transcription text from webhook payload
- [ ] Implement basic NLP or keyword matching on transcriptions to:
  - Detect confirmation ("yes, we received it") → transition referral to `SCHEDULED`
  - Detect missed reason ("I missed it because of the snow") → add to referral notes
  - Detect reschedule request → flag for nurse follow-up
- [ ] Update referral status and notes based on parsed results

---

## Phase 6: Testing

### 6.1 Backend Tests (`backend/tests/`)

- [ ] Set up test fixtures: async test client, test database (SQLite or test PostgreSQL)
- [ ] Referral endpoint tests: create, read, update, state transitions, invalid transitions
- [ ] Patient endpoint tests: create, read, list
- [ ] Weather endpoint tests: mock OpenWeatherMap responses, verify storm detection
- [ ] Voice endpoint tests: mock Vapi calls, test webhook parsing
- [ ] Service layer unit tests: referral state machine, weather threshold logic, SMS formatting
- [ ] Background task tests: mock scheduler jobs, verify safety net and storm mode behavior

### 6.2 Frontend Tests

- [ ] Component tests for forms and tables
- [ ] Integration tests for page data fetching and rendering
- [ ] API service mock tests

---

## Phase 7: Deployment & Infrastructure

### 7.1 Docker & Compose

- [ ] Create `docker-compose.yml` with services: backend, frontend, PostgreSQL
- [ ] Configure environment variable injection from `.env`
- [ ] Add a frontend Dockerfile (Vite build + nginx or similar)

### 7.2 Production Configuration

- [ ] Switch from SQLite/dev database to production PostgreSQL
- [ ] Disable debug mode and auto-reload in production
- [ ] Configure proper CORS origins for production domain
- [ ] Set up health check monitoring

### 7.3 Low-Bandwidth Optimization (TRD Requirement)

- [ ] Optimize frontend bundle size for remote northern connectivity
- [ ] Consider server-side rendering or static pre-rendering for initial load
- [ ] Implement API response compression

---

## Phase 8: Enhancements (Post-MVP)

These are referenced in the PRD/TRD but are secondary to core functionality.

- [ ] **Culturally safe outreach**: Indigenous language support in voice call scripts and SMS templates
- [ ] **Virtual Care links**: Integration with a video conferencing platform for storm-mode rescheduled appointments
- [ ] **Appointment reminders**: Scheduled SMS reminders before upcoming appointments (e.g., 24h and 2h before)
- [ ] **Reporting dashboard**: Metrics on referral closure rates, no-show reduction, and staff time savings
- [ ] **Audit logging**: Track all state changes with timestamps and user attribution
- [ ] **Pre-storm outreach**: 48-hour advance weather prediction to proactively reschedule before highway closures (requires forecast API, not just current conditions)

---

## Recommended Build Order

For the fastest path to a working demo:

1. **Phase 1** (Backend routes) — unlocks API functionality
2. **Phase 2.1** (Alembic migrations) — proper database management
3. **Phase 4.1 + 4.2** (Layout + Dashboard) — visible progress for stakeholders
4. **Phase 4.3** (Referrals page) — core workflow UI
5. **Phase 1.4 + Phase 5** (Voice endpoints + webhook) — Vapi integration
6. **Phase 3** (Security) — required before any real patient data
7. **Phase 6** (Testing) — validate everything works
8. **Phase 7** (Deployment) — go live
