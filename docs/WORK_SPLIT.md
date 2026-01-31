# RidgeCare Link — Team Work Distribution

Phase 1 (Backend API endpoints) is complete. This document splits the remaining work (Phases 2–8) across 4 team members for parallel execution.

---

## Assignments Overview

| Member | Focus Area | Summary |
|--------|-----------|---------|
| **Member 1** | Database, Auth & Security | Alembic migrations, seed data, authentication, authorization, data privacy |
| **Member 2** | Frontend Core & Dashboard | Layout shell, shared components, Dashboard page, Weather page |
| **Member 3** | Frontend Referrals & Patients | Referrals page, Patients page, patient API service wrapper |
| **Member 4** | Vapi Integration, Testing & Deployment | Webhook/NLP processing, full test suite, Docker & production config |

---

## Member 1 — Database, Auth & Security

Backend infrastructure that the rest of the team depends on. This work should start first since other members need the database and seed data to develop against.

### Phase 2: Database & Migrations

- [ ] Configure async engine in `backend/alembic/env.py`
- [ ] Import `Base.metadata` from models so Alembic can detect schema changes
- [ ] Generate the initial migration (`alembic revision --autogenerate`)
- [ ] Verify migration runs cleanly against a fresh PostgreSQL database
- [ ] Create a seed script to populate test patients and referrals for the team to develop against

### Phase 3: Security & Auth

- [ ] Decide on auth strategy (JWT tokens, session-based, or API keys)
- [ ] Implement login endpoint or API key validation
- [ ] Create `get_current_user` dependency in `deps.py` for protecting routes
- [ ] Define role-based access (nurse vs. admin) if needed
- [ ] Apply auth dependencies to all route handlers
- [ ] Ensure patient data encryption at rest (database-level or field-level)
- [ ] Add HTTPS enforcement for production
- [ ] Audit API responses for sensitive data exposure

### Key deliverables
- Working Alembic migrations
- Seed script that the whole team can run
- Auth middleware applied to all protected routes
- Data privacy audit document

### Dependencies
- None (this is the foundation other work builds on)

### Blockers for others
- **Member 2 and Member 3** need the seed script to test frontend pages against real data
- **Member 4** needs auth in place before writing auth-related tests

---

## Member 2 — Frontend Core & Dashboard

Builds the shared UI foundation and the two pages that are less form-heavy: Dashboard and Weather.

### Phase 4.1: Shared Components

- [ ] Create layout shell with navigation sidebar/header (Dashboard, Referrals, Patients, Weather links)
- [ ] Build reusable table component for listing data
- [ ] Build reusable form components (inputs, selects, date pickers)
- [ ] Add loading states and error handling patterns for API calls
- [ ] Add toast/notification system for success and error feedback

### Phase 4.2: Dashboard Page

- [ ] Summary cards: total active referrals, overdue referrals, high-risk patients count
- [ ] Storm Mode status banner (green/red indicator with current weather)
- [ ] Recent activity feed showing latest referral state changes
- [ ] Quick-action buttons (create referral, trigger weather check)

### Phase 4.5: Weather Page

- [ ] Current weather conditions display (temperature, snowfall, description)
- [ ] Storm Mode status with threshold indicators (snow >= 15cm, temp <= -35°C)
- [ ] Active weather alerts list
- [ ] Manual "Activate Storm Mode" override button for nurses
- [ ] Log of recent storm mode activations and actions taken

### Key deliverables
- Layout shell and shared component library that Member 3 can reuse
- Functional Dashboard with live data from backend
- Functional Weather page with storm mode display

### Dependencies
- Needs seed data from **Member 1** to display real data on Dashboard
- None for building component skeletons (can use mock data initially)

### Blockers for others
- **Member 3** depends on the shared components (table, form, layout, toast) being available

---

## Member 3 — Frontend Referrals & Patients

Builds the two most form-heavy and workflow-critical pages. Can start scaffolding immediately but will wire up shared components once Member 2 delivers them.

### Phase 4.3: Referrals Page

- [ ] Referral list table with columns: ticket ID, patient name, status, referred to, scheduled date, action date
- [ ] Status filter (Pending, Scheduled, Attended, Resolved, Missed)
- [ ] Create referral form/modal (patient selection, description, referred to, dates)
- [ ] Referral detail view with status timeline and update form
- [ ] Status transition buttons with validation (only show valid next states)

### Phase 4.4: Patients Page

- [ ] Patient list table with columns: name, phone, high-risk flag, number of active referrals
- [ ] Create/edit patient form (name, phone, DOB, address, high-risk toggle, notes)
- [ ] Patient detail view showing their referral history
- [ ] Add `patientService.ts` API wrapper (currently missing from frontend)

### Key deliverables
- Fully functional Referrals page with create, view, filter, and status transitions
- Fully functional Patients page with create, edit, and referral history
- `patientService.ts` added to `frontend/src/services/`

### Dependencies
- Shared components (table, form, layout) from **Member 2**
- Seed data from **Member 1** for testing with real records

### Blockers for others
- None (end of the frontend chain)

---

## Member 4 — Vapi Integration, Testing & Deployment

Handles the Vapi webhook intelligence, the full test suite, and production deployment. This work is largely independent and can proceed in parallel.

### Phase 5: Vapi Webhook & NLP Processing

- [ ] Define the Vapi webhook payload schema (based on Vapi API docs)
- [ ] Implement webhook handler to parse call status (completed, failed, no-answer)
- [ ] Extract transcription text from webhook payload
- [ ] Implement keyword matching / basic NLP on transcriptions:
  - Detect confirmation → transition referral to `SCHEDULED`
  - Detect missed reason → add to referral notes
  - Detect reschedule request → flag for nurse follow-up
- [ ] Update referral status and notes based on parsed results

### Phase 6: Testing

- [ ] Set up test fixtures: async test client, test database (SQLite or test PostgreSQL)
- [ ] Patient endpoint tests: create, read, list
- [ ] Referral endpoint tests: create, read, update, state transitions, invalid transitions
- [ ] Weather endpoint tests: mock OpenWeatherMap responses, verify storm detection
- [ ] Voice endpoint tests: mock Vapi calls, test webhook parsing
- [ ] Service layer unit tests: referral state machine, weather threshold logic, SMS formatting
- [ ] Background task tests: mock scheduler jobs, verify safety net and storm mode behavior
- [ ] Frontend component tests for forms and tables
- [ ] Frontend integration tests for page data fetching
- [ ] Frontend API service mock tests

### Phase 7: Deployment & Infrastructure

- [ ] Create/finalize `docker-compose.yml` with services: backend, frontend, PostgreSQL
- [ ] Configure environment variable injection from `.env`
- [ ] Add a frontend Dockerfile (Vite build + nginx)
- [ ] Disable debug mode and auto-reload in production config
- [ ] Configure proper CORS origins for production domain
- [ ] Set up health check monitoring
- [ ] Optimize frontend bundle size for low-bandwidth (remote northern connectivity)
- [ ] Implement API response compression

### Key deliverables
- Working Vapi webhook with transcription-based status updates
- Full backend test suite with passing tests
- Frontend test coverage
- Production-ready Docker Compose setup

### Dependencies
- Needs auth from **Member 1** to write auth-aware tests
- Needs frontend pages from **Members 2 & 3** to write frontend tests
- Vapi work and Docker setup can start immediately

### Blockers for others
- None (this is the final validation and deployment layer)

---

## Parallel Execution Timeline

```
Member 1 ──[Alembic + Seed]──────[Auth + Security]──────────[Privacy Audit]──
Member 2 ──[Layout + Shared Components]──[Dashboard]──[Weather Page]─────────
Member 3 ──[patientService.ts]──[Patients Page]──[Referrals Page]────────────
Member 4 ──[Vapi Webhook/NLP]──[Docker Setup]──[Backend Tests]──[FE Tests]──
                │                     │                │              │
                ▼                     ▼                ▼              ▼
           Seed data ready     Components ready   Pages ready    All tested
```

### Coordination points

1. **Member 1** should deliver the seed script early so Members 2 and 3 can test with real data
2. **Member 2** should deliver shared components before Member 3 starts wiring up pages
3. **Member 4** should start with Vapi webhook + Docker (no dependencies), then write tests once other members' code is available
4. All members should agree on the auth strategy before Member 1 implements it

---

## Phase 8: Post-MVP (Whole Team)

These enhancements can be picked up by anyone after the MVP is complete:

- [ ] Culturally safe outreach — Indigenous language support in voice/SMS templates
- [ ] Virtual Care links — Video conferencing integration for storm-mode rescheduling
- [ ] Appointment reminders — Scheduled SMS reminders (24h and 2h before)
- [ ] Reporting dashboard — Referral closure rates, no-show reduction, staff time metrics
- [ ] Audit logging — State change tracking with timestamps and user attribution
- [ ] Pre-storm outreach — 48-hour forecast prediction for proactive rescheduling
