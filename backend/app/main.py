import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.middleware import HTTPSRedirectMiddleware

from app.api.routes import auth, referrals, weather, voice, patients, facilities, storm_mode, appointments
from app.core.config import settings
from app.db.session import engine
from app.models import base
from app.tasks import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables, start background scheduler on startup, stop on shutdown."""
    retries = 10
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(base.Base.metadata.create_all)
            break
        except OSError:
            if attempt == retries:
                raise
            logger.warning("DB not ready, retrying (%d/%d)...", attempt, retries)
            await asyncio.sleep(2)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="RidgeCare Link API",
    version="0.1.0",
    description="Closed-loop referral management platform for Clearwater Ridge",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])
app.include_router(facilities.router, prefix="/api/facilities", tags=["facilities"])
app.include_router(storm_mode.router, prefix="/api/storm-mode", tags=["storm-mode"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
