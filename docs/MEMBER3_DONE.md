# Member 3 — What Was Done

## Part 3: Authentication (JWT)

### New Files
- `backend/app/models/user.py` — User model (username, hashed_password, full_name, role, is_active)
- `backend/app/schemas/auth.py` — LoginRequest and TokenResponse schemas
- `backend/app/api/routes/auth.py` — `POST /api/auth/login` endpoint

### Modified Files
- `backend/requirements.txt` — added `python-jose[cryptography]`, `passlib[bcrypt]`
- `backend/app/core/config.py` — added `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`
- `backend/.env.example` — added `SECRET_KEY=`
- `backend/app/core/security.py` — implemented `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- `backend/app/api/deps.py` — implemented `get_current_user` dependency and `require_role` factory
- `backend/app/main.py` — registered auth router at `/api/auth`
- `backend/alembic/env.py` — added User model import
- `backend/scripts/seed.py` — seeds 2 users (admin + nurse)

### Protected Endpoints
- `patients.py` — all 3 endpoints
- `referrals.py` — all 4 endpoints
- `weather.py` — both endpoints
- `voice.py` — 2 nurse-facing endpoints (webhook left unprotected)

### Left Unprotected
- `GET /health`
- `POST /api/auth/login`
- `POST /api/voice/webhook`

### Seed Users
- `admin` / `changeme123` (role: admin)
- `nurse.adams` / `changeme123` (role: nurse)

### To Activate
```bash
pip install python-jose[cryptography] passlib[bcrypt]
cd backend
alembic revision --autogenerate -m "create users table"
alembic upgrade head
python -m scripts.seed
```
