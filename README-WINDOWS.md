# RidgeCare Link - Windows Installation Guide


## Tech Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Voice/NLP:** Vapi AI API
- **SMS:** Twilio API
- **Weather:** OpenWeatherMap API

## Prerequisites

- **Node.js** (v18+)
- **Python** (3.11+)
- **PostgreSQL** (16+)

### Installing PostgreSQL on Windows

**Option 1: Using winget (Package Manager)**

```powershell
winget install PostgreSQL.PostgreSQL.16
```

**Option 2: Download Installer**

1. Go to https://www.postgresql.org/download/windows/
2. Download PostgreSQL 16
3. Run the installer and follow the setup wizard
4. Remember the password you set for the `postgres` user

**Verify Installation:**

```powershell
psql --version
```

Add PostgreSQL to PATH if needed (usually done automatically during installation).

## Setup

### 1. Clone the repo

```powershell
git clone <repo-url>
cd ClearCare
```

### 2. Create the database

```powershell
psql -U postgres -c "CREATE DATABASE ridgecare;"
```

You'll be prompted for the postgres password you set during installation.

### 3. Backend setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` file from the template:

```powershell
copy .env.example .env
```

Edit `backend/.env` and update the `DATABASE_URL`:

```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ridgecare
```

Replace `YOUR_PASSWORD` with the postgres password you set during PostgreSQL installation.

### 4. Frontend setup

```powershell
cd frontend
npm install
```

## Running

Open two PowerShell terminal windows in the project root:

**Terminal 1 — Backend:**

```powershell
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. Database tables are auto-created on first startup.

**Terminal 2 — Frontend:**

```powershell
cd frontend
npm run dev
```

Frontend runs at http://localhost:5173.

### Verify it works

```powershell
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

API docs are at http://localhost:8000/docs.

## Running with Docker (alternative)

If you have Docker Desktop installed:

1. Create `backend/.env`, but set:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ridgecare
   ```

2. Run:
   ```powershell
   docker-compose up --build
   ```

This starts PostgreSQL, backend, and frontend together.

## API Keys

The app starts without API keys. Add them to `backend/.env` when ready:

| Key | Service | Get it from |
|-----|---------|-------------|
| `VAPI_API_KEY` | Vapi AI (voice calls) | https://vapi.ai |
| `TWILIO_ACCOUNT_SID` | Twilio (SMS) | https://twilio.com/console |
| `TWILIO_AUTH_TOKEN` | Twilio (SMS) | https://twilio.com/console |
| `TWILIO_PHONE_NUMBER` | Twilio (SMS) | https://twilio.com/console |
| `WEATHER_API_KEY` | OpenWeatherMap | https://openweathermap.org/api |

## Project Structure

```
ClearCare/
├── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── Dockerfile
│   ├── alembic/                 # DB migrations
│   └── app/
│       ├── main.py              # FastAPI app + lifespan
│       ├── api/routes/          # HTTP endpoints
│       │   ├── referrals.py     # CRUD for referral tickets
│       │   ├── patients.py      # CRUD for patients
│       │   ├── weather.py       # Weather status endpoints
│       │   └── voice.py         # Vapi call triggers + webhook
│       ├── core/
│       │   ├── config.py        # Settings (env vars, thresholds)
│       │   └── security.py      # Auth
│       ├── db/
│       │   └── session.py       # Async SQLAlchemy engine
│       ├── models/              # SQLAlchemy models
│       │   ├── patient.py
│       │   └── referral.py      # Includes state machine enum
│       ├── schemas/             # Pydantic request/response schemas
│       │   ├── patient.py
│       │   └── referral.py
│       ├── services/            # Business logic
│       │   ├── referral_service.py  # Ticket creation, state transitions
│       │   ├── weather_service.py   # OpenWeatherMap polling
│       │   ├── voice_service.py     # Vapi AI outbound calls
│       │   └── sms_service.py       # Twilio SMS
│       └── tasks/               # Background scheduled jobs
│           ├── __init__.py      # APScheduler setup
│           ├── weather_poller.py    # Polls weather every 30 min
│           ├── safety_net.py        # Checks overdue referrals every hour
│           └── storm_mode.py        # SMS + voice rescheduling on severe weather
└── frontend/
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── App.tsx
        ├── pages/
        │   ├── DashboardPage.tsx
        │   ├── PatientsPage.tsx
        │   ├── ReferralsPage.tsx
        │   └── WeatherPage.tsx
        ├── components/
        │   ├── common/
        │   ├── dashboard/
        │   ├── referrals/
        │   └── weather/
        └── services/
            ├── api.ts
            ├── referralService.ts
            └── weatherService.ts
```
