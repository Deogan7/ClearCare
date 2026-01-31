# Backend Documentation

## Directory Structure

```
backend/
├── app/                          # Main application package
│   ├── __init__.py               # Package initializer
│   ├── main.py                   # FastAPI application entry point
│   ├── core/                     # Core configuration and security
│   │   ├── config.py             # Centralized app settings
│   │   └── security.py           # Auth utilities (placeholder)
│   ├── db/                       # Database session management
│   │   └── session.py            # Async engine and session factory
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── base.py               # Declarative base class
│   │   ├── patient.py            # Patient model
│   │   └── referral.py           # Referral model + status enum
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── patient.py            # Patient validation models
│   │   └── referral.py           # Referral validation models
│   ├── api/                      # REST API routes and dependencies
│   │   ├── deps.py               # Shared FastAPI dependencies (placeholder)
│   │   └── routes/
│   │       ├── patients.py       # Patient CRUD endpoints
│   │       ├── referrals.py      # Referral ticket endpoints
│   │       ├── weather.py        # Weather monitoring endpoints
│   │       └── voice.py          # Vapi AI voice call endpoints
│   ├── services/                 # Business logic layer
│   │   ├── referral_service.py   # Referral state machine and queries
│   │   ├── weather_service.py    # OpenWeatherMap integration
│   │   ├── sms_service.py        # Twilio SMS integration
│   │   └── voice_service.py      # Vapi AI voice call integration
│   └── tasks/                    # Background jobs and scheduler
│       ├── __init__.py           # APScheduler setup and lifecycle
│       ├── weather_poller.py     # Periodic weather monitoring
│       ├── storm_mode.py         # Severe weather response workflow
│       └── safety_net.py         # Missed appointment detection
├── tests/
│   └── test_referrals.py         # Referral test suite (placeholder)
├── alembic/                      # Database migration configuration
│   └── env.py                    # Alembic environment setup
├── alembic.ini                   # Alembic config file
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container image definition
└── .env.example                  # Environment variables template
```

---

## Core Application

### `app/main.py`

The FastAPI application entry point. Creates the app instance titled "RidgeCare Link API" and wires everything together:

- **`lifespan()`** — Async context manager that creates database tables on startup and manages the APScheduler lifecycle (start on boot, shutdown on exit).
- Configures CORS middleware using origins from settings.
- Registers four API routers: referrals, patients, weather, and voice.
- Exposes a `/health` endpoint for health checks.

---

## Configuration (`app/core/`)

### `config.py`

Centralized configuration using Pydantic Settings, loaded from a `.env` file. Key groups:

| Group | Variables |
|-------|-----------|
| App | `APP_NAME`, `DEBUG` |
| Database | `DATABASE_URL` (PostgreSQL async connection string) |
| Vapi AI | `VAPI_API_KEY`, `VAPI_BASE_URL` |
| Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| Weather | `WEATHER_API_KEY`, `WEATHER_API_BASE_URL`, `WEATHER_LOCATION_LAT`, `WEATHER_LOCATION_LON` |
| Storm Mode | `SNOW_THRESHOLD_CM` (15.0), `TEMP_THRESHOLD_C` (-35.0) |
| Safety Net | `SAFETY_NET_HOURS` (48) |
| CORS | `CORS_ORIGINS` (defaults to `["http://localhost:5173"]`) |

### `security.py`

Placeholder for future authentication and authorization utilities.

---

## Database Layer (`app/db/`)

### `session.py`

Manages the async database connection using SQLAlchemy's async engine with the AsyncPG driver.

- **`engine`** — `AsyncEngine` created from `DATABASE_URL`.
- **`async_session`** — Session factory for creating async database sessions.
- **`get_db()`** — Async generator used as a FastAPI dependency to inject database sessions into route handlers.

---

## Models (`app/models/`)

### `base.py`

Defines the SQLAlchemy `DeclarativeBase` class that all ORM models inherit from.

### `patient.py`

The `patients` table. Represents healthcare recipients.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `first_name`, `last_name` | String | Patient name |
| `phone` | String | Contact number for SMS/voice |
| `date_of_birth` | DateTime | Optional |
| `is_high_risk` | Boolean | Flag for priority weather/safety alerts |
| `address` | String | Optional location |
| `notes` | String | Clinical notes |
| `created_at`, `updated_at` | DateTime | Auto-managed timestamps |

Has a one-to-many relationship with `Referral`.

### `referral.py`

The `referrals` table. Represents referral tickets for medical appointments.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `ticket_id` | String | Human-readable ID (e.g., "RC-A1B2C3") |
| `patient_id` | UUID | Foreign key to `patients` |
| `status` | Enum | Current referral state |
| `description`, `notes` | String | Appointment details |
| `referred_to` | String | Destination provider/facility |
| `action_date`, `scheduled_date` | DateTime | Key dates |
| `created_by` | String | Nurse identifier |
| `created_at`, `updated_at` | DateTime | Auto-managed timestamps |

**`ReferralStatus` enum:**

- `PENDING_CONFIRMATION` — Initial state after creation
- `SCHEDULED` — Appointment confirmed
- `ATTENDED` — Patient attended
- `RESOLVED` — Complete and closed
- `MISSED` — Patient missed (triggers safety net)

---

## Schemas (`app/schemas/`)

Pydantic models used for API request validation and response serialization.

### `patient.py`

- **`PatientBase`** — Shared fields (name, phone, date of birth, risk flag, address, notes).
- **`PatientCreate`** — Extends base for POST requests.
- **`PatientUpdate`** — All fields optional for PATCH requests.
- **`PatientResponse`** — Adds `id`, `created_at`, `updated_at` for API responses.

### `referral.py`

- **`ReferralBase`** — Shared fields (patient_id, description, referred_to, dates, notes).
- **`ReferralCreate`** — Adds `created_by` for new referral creation.
- **`ReferralUpdate`** — Optional fields for status/date/notes updates.
- **`ReferralResponse`** — Adds `id`, `ticket_id`, `status`, timestamps for API responses.

---

## API Routes (`app/api/routes/`)

### `patients.py`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/patients/` | List all patients |
| `POST` | `/api/patients/` | Create a new patient |
| `GET` | `/api/patients/{patient_id}` | Get patient by ID |

*Stub implementations — business logic pending.*

### `referrals.py`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/referrals/` | List all active referral tickets |
| `POST` | `/api/referrals/` | Create a new referral ticket |
| `GET` | `/api/referrals/{ticket_id}` | Get referral by ticket ID |
| `PATCH` | `/api/referrals/{ticket_id}` | Update referral status/details |

*Stub implementations — business logic pending.*

### `weather.py`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/weather/current` | Fetch current weather for configured location |
| `GET` | `/api/weather/storm-status` | Check storm mode threshold status |

*Stub implementations — business logic pending.*

### `voice.py`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/voice/verify-referral/{ticket_id}` | Trigger outbound verification call to hospital admin |
| `POST` | `/api/voice/patient-checkin/{patient_id}` | Trigger wellness check-in call to patient |
| `POST` | `/api/voice/webhook` | Receive call status/transcription updates from Vapi |

*Stub implementations — business logic pending.*

### `deps.py`

Placeholder for shared FastAPI dependencies (auth, pagination, etc.).

---

## Services (`app/services/`)

### `referral_service.py`

Core referral management logic with a state machine enforcing valid status transitions:

```
PENDING_CONFIRMATION → SCHEDULED, MISSED
SCHEDULED            → ATTENDED, MISSED
ATTENDED             → RESOLVED
RESOLVED             → (terminal)
MISSED               → SCHEDULED
```

Key functions:

- **`create_referral()`** — Creates a referral with a generated ticket ID and `PENDING_CONFIRMATION` status.
- **`transition_status()`** — Validates and applies state transitions; raises `ValueError` on invalid moves.
- **`update_referral()`** — Updates referral fields with optional status transition.
- **`get_overdue_referrals()`** — Finds `SCHEDULED` referrals past the 48-hour safety net window.
- **`get_upcoming_referrals()`** — Gets `SCHEDULED` referrals within the next 72 hours.
- **`get_high_risk_patients_with_upcoming()`** — Joins patients and referrals to find high-risk patients with upcoming appointments.

### `weather_service.py`

OpenWeatherMap API integration. Determines severe weather based on configurable thresholds.

- **`fetch_current_weather()`** — Polls the weather API and returns a `WeatherCondition` dataclass with temperature, snowfall, description, and severity flag.
- **`check_weather_alerts()`** — Fetches active weather alerts from the OneCall API.
- **Severe weather** is defined as snow >= 15 cm OR temperature <= -35 C.

### `sms_service.py`

Twilio integration for outbound SMS messages. Provides pre-formatted message templates:

- **`send_sms()`** — Generic SMS sending.
- **`send_storm_checkin_sms()`** — Weather emergency check-in for high-risk patients.
- **`send_appointment_reminder()`** — Appointment reminder with ticket ID and date.
- **`send_virtual_care_link()`** — Delivers a virtual care session link.

### `voice_service.py`

Vapi AI integration for outbound voice calls via async HTTP (httpx):

- **`verify_referral_receipt()`** — Calls hospital admin to confirm referral document receipt.
- **`initiate_patient_follow_up_call()`** — Follow-up call for missed appointments.
- **`initiate_reschedule_call()`** — Reschedule physical visit to virtual care due to weather.

Each call includes metadata (ticket_id, call_type) for tracking.

---

## Background Tasks (`app/tasks/`)

### `__init__.py`

Initializes the APScheduler `AsyncIOScheduler` and registers two periodic jobs:

| Job | Interval | Description |
|-----|----------|-------------|
| `poll_weather` | 30 minutes | Checks for severe weather conditions |
| `check_safety_net` | 1 hour | Detects missed/overdue appointments |

Provides `start_scheduler()` and `stop_scheduler()` lifecycle functions called from `main.py`'s lifespan handler.

### `weather_poller.py`

Runs every 30 minutes. Fetches current weather via the weather service, logs conditions, and triggers `activate_storm_mode()` if severity thresholds are exceeded.

### `storm_mode.py`

Activated when severe weather is detected. For every high-risk patient with upcoming appointments:

1. Sends a storm check-in SMS via Twilio.
2. Initiates a Vapi reschedule call to convert the physical visit to virtual care.

### `safety_net.py`

Runs every hour. Scans for `SCHEDULED` referrals past the 48-hour safety window:

1. Transitions overdue referrals to `MISSED` status.
2. Initiates automated follow-up voice calls to affected patients.

---

## Infrastructure Files

### `requirements.txt`

Key dependencies: FastAPI, Uvicorn, SQLAlchemy (async), AsyncPG, Pydantic, Alembic, HTTPX, Twilio, APScheduler, python-dotenv.

### `Dockerfile`

Builds from `python:3.12-slim`. Installs dependencies, copies application code, and runs Uvicorn on port 8000 with auto-reload.

### `alembic.ini` / `alembic/env.py`

Alembic database migration configuration. The environment file is a placeholder awaiting async engine setup.

### `.env.example`

Template for required environment variables: database URL, Vapi API key, Twilio credentials, and weather API key.

---

## Architecture Overview

```
                         ┌─────────────────┐
                         │   API Requests   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     Routes (API Layer)     │
                    │  patients, referrals,      │
                    │  weather, voice             │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   Services (Business Logic)│
                    │  referral_service           │
                    │  weather_service            │
                    │  sms_service                │
                    │  voice_service              │
                    └──────┬──────────┬─────────┘
                           │          │
              ┌────────────┘          └────────────┐
              │                                    │
     ┌────────┴────────┐              ┌────────────┴────────┐
     │  Models (ORM)   │              │ External Services    │
     │  Patient        │              │ OpenWeatherMap       │
     │  Referral       │              │ Twilio SMS           │
     └────────┬────────┘              │ Vapi AI Voice        │
              │                       └─────────────────────┘
     ┌────────┴────────┐
     │   PostgreSQL    │
     └─────────────────┘
```

### Background Task Flow

```
APScheduler (started at app boot)
  ├── poll_weather (every 30 min)
  │     └── severe? → activate_storm_mode()
  │                     ├── SMS to high-risk patients
  │                     └── Reschedule calls via Vapi
  │
  └── check_safety_net (every 1 hour)
        ├── Mark overdue referrals as MISSED
        └── Follow-up calls via Vapi
```
