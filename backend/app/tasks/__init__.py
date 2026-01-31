"""Background task scheduler using APScheduler.

Provides a single AsyncIOScheduler instance shared across the application.
Tasks are registered in their respective modules and started via `start_scheduler()`.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Register all periodic jobs and start the scheduler."""
    from app.tasks.weather_poller import poll_weather
    from app.tasks.safety_net import check_safety_net

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

    scheduler.start()


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
