# ClearCare Link


## Tech Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **Voice/NLP:** Vapi AI API
- **SMS:** Twilio API
- **Weather:** WeatherAPI.com

## Prerequisites

- **Node.js** (v18+)
- **Python** (3.11+)
- **PostgreSQL** (16+)

### Installing PostgreSQL (macOS)

```bash
brew install postgresql@16
brew services start postgresql@16
```

Add to your PATH if needed:

```bash
echo 'export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd ClearCare
```

### 2. Create the database

```bash
createdb ridgecare
```

### 3. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Edit `backend/.env` and update the `DATABASE_URL` with your macOS username:

```
DATABASE_URL=postgresql+asyncpg://YOUR_USERNAME@localhost:5432/ridgecare
```

To find your username, run `whoami`.

### 4. Frontend setup

```bash
cd frontend
npm install
```

## Running

Open two terminal windows:

**Terminal 1 — Backend (from project root):**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000. Database tables are auto-created on first startup.

**Terminal 2 — Frontend (from project root):**

```bash
cd frontend
npm run dev
```

Frontend runs at http://localhost:5173.

### Verify it works

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

API docs are at http://localhost:8000/docs.

## Running with Docker (alternative)

If you have Docker Desktop installed:

1. Create `backend/.env` (see step 3 above), but set:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ridgecare
   ```

2. Run:
   ```bash
   docker compose up --build
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
| `WEATHER_API_KEY` | WeatherAPI.com | https://www.weatherapi.com/ |
| `WEATHER_API_BASE_URL` | WeatherAPI.com | http://api.weatherapi.com/v1 |

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
