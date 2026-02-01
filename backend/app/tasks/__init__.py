"""Background task scheduler using APScheduler.

Provides a single AsyncIOScheduler instance shared across the application.
Tasks are registered in their respective modules and started via `start_scheduler()`.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Register all periodic jobs and start the scheduler."""
    from app.tasks.weather_poller import poll_weather
    from app.tasks.safety_net import check_safety_net
    from app.tasks.workflow_engine import run_workflow_engine

    # In demo mode, run the workflow engine every 1 minute so calls chain fast.
    workflow_interval = 1 if settings.DEMO_MODE else 15

    # Poll weather every 30 minutes.
    scheduler.add_job(
        poll_weather,
        trigger=IntervalTrigger(minutes=30),
        id="weather_poller",
        replace_existing=True,
    )

    # Check for overdue referrals every hour.
    scheduler.add_job(
        check_safety_net,
        trigger=IntervalTrigger(hours=1),
        id="safety_net_check",
        replace_existing=True,
    )

    # Run the referral workflow engine.
    scheduler.add_job(
        run_workflow_engine,
        trigger=IntervalTrigger(minutes=workflow_interval),
        id="workflow_engine",
        replace_existing=True,
    )

    if settings.DEMO_MODE:
        logger.info("DEMO MODE: Workflow engine running every %d minute(s).", workflow_interval)

    scheduler.start()


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
