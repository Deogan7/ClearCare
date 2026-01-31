# Member 1 Guide — Database, Auth & Security

Step-by-step implementation guide for everything in Member 1's responsibilities. Each section tells you exactly which files to create or modify, what code to write, and how to verify your work.

---

## Part 1: Alembic Async Configuration

The Alembic environment file at `backend/alembic/env.py` is currently empty. It needs to be configured to work with the async PostgreSQL engine.

### 1.1 Add missing Alembic template files

Alembic expects a `versions/` directory and a `script.py.mako` template. Create them:

```bash
mkdir -p backend/alembic/versions
```

Create `backend/alembic/script.py.mako`:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

### 1.2 Write the async `env.py`

Replace the contents of `backend/alembic/env.py` with:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models.base import Base

# Import all models so Base.metadata knows about them
from app.models.patient import Patient      # noqa: F401
from app.models.referral import Referral    # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL to stdout)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

**What this does:**
- Imports `Base.metadata` and all model classes so Alembic can see the `patients` and `referrals` tables
- Overrides the `sqlalchemy.url` from `alembic.ini` with the value from `settings.DATABASE_URL` (so the `.env` file is the single source of truth)
- Uses `create_async_engine` + `run_sync` to run migrations through the async driver

### 1.3 Generate the initial migration

Make sure PostgreSQL is running and the `ridgecare` database exists:

```bash
createdb ridgecare   # skip if it already exists
```

Then from the `backend/` directory:

```bash
cd backend
alembic revision --autogenerate -m "create patients and referrals tables"
```

This will generate a file in `backend/alembic/versions/` with the `CREATE TABLE` statements for both `patients` and `referrals`.

### 1.4 Run the migration

```bash
alembic upgrade head
```

### 1.5 Verify

Connect to the database and confirm both tables exist:

```bash
psql ridgecare -c "\dt"
```

You should see `patients`, `referrals`, and `alembic_version` tables.

---

## Part 2: Seed Script

Create `backend/scripts/seed.py`. This gives the whole team test data to develop against.

```python
"""Seed the database with test patients and referrals for development."""

import asyncio
import uuid
from datetime import datetime, timedelta

from app.db.session import async_session
from app.models.patient import Patient
from app.models.referral import Referral
from app.models.referral import ReferralStatus


async def seed():
    async with async_session() as db:
        # -- Patients --
        p1 = Patient(
            id=uuid.uuid4(),
            first_name="Margaret",
            last_name="Blackwood",
            phone="+14035551001",
            date_of_birth=datetime(1948, 3, 15),
            is_high_risk=True,
            address="12 Pine Crescent, Clearwater Ridge",
            notes="Hypertension, limited mobility. Lives alone.",
        )
        p2 = Patient(
            id=uuid.uuid4(),
            first_name="James",
            last_name="Whitehorse",
            phone="+14035551002",
            date_of_birth=datetime(1955, 11, 2),
            is_high_risk=True,
            address="45 River Road, Clearwater Ridge",
            notes="Diabetes type 2, requires regular cardiology follow-up.",
        )
        p3 = Patient(
            id=uuid.uuid4(),
            first_name="Sarah",
            last_name="Morin",
            phone="+14035551003",
            date_of_birth=datetime(1972, 7, 20),
            is_high_risk=False,
            address="8 Elk Avenue, Clearwater Ridge",
            notes="",
        )
        p4 = Patient(
            id=uuid.uuid4(),
            first_name="David",
            last_name="Cardinal",
            phone="+14035551004",
            date_of_birth=datetime(1940, 1, 8),
            is_high_risk=True,
            address="22 Spruce Lane, Clearwater Ridge",
            notes="Post-stroke rehabilitation. Needs accessible transport.",
        )

        db.add_all([p1, p2, p3, p4])
        await db.flush()

        # -- Referrals --
        now = datetime.utcnow()

        r1 = Referral(
            ticket_id="RC-SEED01",
            patient_id=p1.id,
            status=ReferralStatus.PENDING_CONFIRMATION,
            description="Cardiology follow-up for irregular heartbeat",
            referred_to="Calgary Foothills Cardiology",
            action_date=now + timedelta(days=7),
            scheduled_date=None,
            notes="Awaiting hospital confirmation.",
            created_by="Nurse Adams",
        )
        r2 = Referral(
            ticket_id="RC-SEED02",
            patient_id=p2.id,
            status=ReferralStatus.SCHEDULED,
            description="Endocrinology consult for diabetes management",
            referred_to="Red Deer Regional Hospital",
            action_date=now + timedelta(days=3),
            scheduled_date=now + timedelta(days=5),
            notes="Transport arranged via community van.",
            created_by="Nurse Adams",
        )
        r3 = Referral(
            ticket_id="RC-SEED03",
            patient_id=p3.id,
            status=ReferralStatus.ATTENDED,
            description="Routine ortho follow-up for knee replacement",
            referred_to="Calgary Ortho Clinic",
            action_date=now - timedelta(days=10),
            scheduled_date=now - timedelta(days=7),
            notes="Patient attended. Awaiting discharge summary.",
            created_by="Nurse Chen",
        )
        r4 = Referral(
            ticket_id="RC-SEED04",
            patient_id=p4.id,
            status=ReferralStatus.MISSED,
            description="Neurology follow-up post-stroke",
            referred_to="Calgary Stroke Centre",
            action_date=now - timedelta(days=5),
            scheduled_date=now - timedelta(days=2),
            notes="Highway closed due to storm. Needs rescheduling.",
            created_by="Nurse Adams",
        )

        db.add_all([r1, r2, r3, r4])
        await db.commit()

    print("Seeded 4 patients and 4 referrals.")


if __name__ == "__main__":
    asyncio.run(seed())
```

**Run with:**

```bash
cd backend
python -m scripts.seed
```

**Verify:**

```bash
psql ridgecare -c "SELECT ticket_id, status FROM referrals;"
```

---

## Part 3: Authentication (JWT)

JWT is the recommended approach — it's stateless, works well with the REST API, and doesn't require server-side session storage.

### 3.1 Add dependencies

Add these to `backend/requirements.txt`:

```
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
```

Then install:

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

### 3.2 Add config values

Add these fields to the `Settings` class in `backend/app/core/config.py`:

```python
# Auth
SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hour shift
ALGORITHM: str = "HS256"
```

Also add `SECRET_KEY=` to `backend/.env.example` so team members know to set it.

### 3.3 Create a User model

Create `backend/app/models/user.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="nurse")  # "nurse" or "admin"
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

After creating this file, add the import to `alembic/env.py`:

```python
from app.models.user import User  # noqa: F401
```

Then generate and apply the migration:

```bash
alembic revision --autogenerate -m "create users table"
alembic upgrade head
```

### 3.4 Implement security utilities

Replace the contents of `backend/app/core/security.py`:

```python
"""Authentication and authorization utilities."""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

### 3.5 Create auth schemas

Create `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### 3.6 Create the auth route

Create `backend/app/api/routes/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)
```

Register the router in `backend/app/main.py` by adding:

```python
from app.api.routes import auth
```

and:

```python
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
```

### 3.7 Create the `get_current_user` dependency

Replace the contents of `backend/app/api/deps.py`:

```python
"""Shared FastAPI dependencies (auth, pagination, etc.)."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT and return the authenticated User, or 401."""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_role(role: str):
    """Dependency factory: require a specific role."""
    async def _check(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(status_code=403, detail=f"Requires {role} role")
        return user
    return _check
```

### 3.8 Apply auth to route handlers

Add `Depends(get_current_user)` to every route that needs protection. Example for `patients.py`:

**Before:**
```python
async def list_patients(db: AsyncSession = Depends(get_db)):
```

**After:**
```python
from app.api.deps import get_current_user
from app.models.user import User

async def list_patients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
```

Do this for every endpoint in:
- `backend/app/api/routes/patients.py` — all 3 endpoints
- `backend/app/api/routes/referrals.py` — all 4 endpoints
- `backend/app/api/routes/weather.py` — all 2 endpoints
- `backend/app/api/routes/voice.py` — all 3 endpoints

The `/api/auth/login` endpoint and `/health` endpoint should remain **unprotected**.

For admin-only endpoints (if any), use `require_role("admin")` instead of `get_current_user`.

### 3.9 Seed an initial admin user

Add this to the bottom of `backend/scripts/seed.py` (inside the `seed()` function, before the final `commit()`):

```python
from app.models.user import User
from app.core.security import hash_password

admin = User(
    username="admin",
    hashed_password=hash_password("changeme123"),
    full_name="System Administrator",
    role="admin",
)
nurse = User(
    username="nurse.adams",
    hashed_password=hash_password("changeme123"),
    full_name="Nurse Adams",
    role="nurse",
)
db.add_all([admin, nurse])
```

---

## Part 4: Data Privacy & Security Hardening

### 4.1 HTTPS enforcement

Create `backend/app/core/middleware.py`:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from app.core.config import settings


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.DEBUG and request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)
        return await call_next(request)
```

Register in `main.py`:

```python
from app.core.middleware import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)
```

This only redirects in production (`DEBUG=False`), so local development is unaffected.

### 4.2 Database encryption at rest

PostgreSQL supports Transparent Data Encryption (TDE) at the instance level. For this project, the practical steps are:

1. **Enable SSL on the PostgreSQL connection** — update `DATABASE_URL` in production:
   ```
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/ridgecare?ssl=require
   ```

2. **Ensure the production PostgreSQL volume is on an encrypted disk** (AWS EBS encryption, Azure disk encryption, etc.). This is an infrastructure concern, not application code.

3. **Do not log patient data** — audit the codebase for any `logger.info()` or `print()` calls that output patient names, phone numbers, or notes. The existing service files log ticket IDs only, which is fine.

### 4.3 Audit API responses for sensitive data exposure

Review every `*Response` schema in `backend/app/schemas/` and confirm:

- `PatientResponse` — currently exposes all fields. Consider whether `phone` should be masked in list endpoints (e.g., `***-**-1001`). If masking is needed, add a computed field in the schema.
- `ReferralResponse` — currently fine, no sensitive fields beyond what nurses need.
- Never return `hashed_password` or `User` objects directly. The `TokenResponse` schema only returns the JWT, which is correct.

Create a short document at `docs/PRIVACY_AUDIT.md` listing what you checked and any decisions made.

### 4.4 Add security headers

Add to `main.py` after the CORS middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

## Verification Checklist

After completing all parts, verify each deliverable:

- [ ] `alembic upgrade head` runs without errors on a fresh database
- [ ] `alembic downgrade base` and `alembic upgrade head` is idempotent
- [ ] `python -m scripts.seed` populates 4 patients, 4 referrals, and 2 users
- [ ] `POST /api/auth/login` with `{"username": "admin", "password": "changeme123"}` returns a JWT
- [ ] `GET /api/patients/` without a token returns `403`
- [ ] `GET /api/patients/` with `Authorization: Bearer <token>` returns the seeded patients
- [ ] `GET /health` works without auth
- [ ] No patient PII appears in server logs during normal requests
- [ ] `docs/PRIVACY_AUDIT.md` is written and committed
