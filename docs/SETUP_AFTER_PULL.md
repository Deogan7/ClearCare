# Setup After Pull

## What Changed

### Part 3: JWT Authentication
- Added `POST /api/auth/login` endpoint that returns a Bearer token
- All endpoints (except `/health`, `/api/auth/login`, `/api/voice/webhook`) now require a valid JWT in the `Authorization` header
- Two seed users: `admin` / `changeme123` and `nurse.adams` / `changeme123`
- Tokens expire after 8 hours (one nursing shift)

### Part 4: Security Hardening
- HTTPS redirect middleware (active when `DEBUG=False`)
- Security headers on all responses: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`
- Privacy audit documented in `docs/PRIVACY_AUDIT.md`

---

## Steps to Run

### 1. Start the database

```bash
docker compose up -d db
```

Wait a few seconds for PostgreSQL to become healthy.

### 2. Activate the virtual environment

macOS/Linux:

```bash
cd backend
source venv/bin/activate
```

Windows (PowerShell):

```powershell
cd backend
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install "bcrypt==4.0.1"
```

The bcrypt pin is needed because `passlib` is not compatible with bcrypt 4.1+.

### 4. Set the database URL

The `.env` file uses `db` as the hostname (for Docker Compose networking). When running locally outside Docker, override it:

macOS/Linux:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ridgecare
```

Windows (PowerShell):

```powershell
$env:DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/ridgecare"
```

### 5. Run migrations

```bash
PYTHONPATH=. alembic upgrade head
```

This creates the `patients`, `referrals`, and `users` tables.

### 6. Seed the database

```bash
PYTHONPATH=. python -m scripts.seed
```

Seeds 4 patients, 4 referrals, and 2 users (admin + nurse).

### 7. Start the server

```bash
PYTHONPATH=. uvicorn app.main:app --reload
```

Server runs at http://localhost:8000. Swagger docs at http://localhost:8000/docs.

---

## Testing Auth

```bash
# Login
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"changeme123"}'

# Use the token from the response
curl -s http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer <paste_token_here>"
```

---

## Notes

- Add a real `SECRET_KEY` in `.env` for production (do not use the default)
- The voice webhook (`POST /api/voice/webhook`) is intentionally unprotected -- it is called by the external Vapi service
- If your local PostgreSQL is running on port 5432, stop it first so the Docker container can bind to that port
