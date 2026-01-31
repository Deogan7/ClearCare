import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import referrals, weather, voice, patients
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

app.include_router(referrals.router, prefix="/api/referrals", tags=["referrals"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
app.include_router(voice.router, prefix="/api/voice", tags=["voice"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
