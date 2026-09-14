"""Sets up and manages the background job scheduler (APScheduler).
Runs periodic environmental data polling independent of user requests."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.supabase_client import get_supabase
from app.jobs.poll_air_quality import poll_air_quality_job
from app.jobs.poll_weather import poll_weather_job

logger = logging.getLogger(__name__)

# TODO: replace this hardcoded list with distinct regions pulled from the 
# users table once there's enough real user data to make that worthwhile.
TRACKED_REGIONS = ["Jaipur", "Jodhpur", "Udaipur"]

scheduler = BackgroundScheduler()


def _run_air_quality_job():
    db = get_supabase()
    poll_air_quality_job(db, TRACKED_REGIONS)


def _run_weather_job():
    db = get_supabase()
    poll_weather_job(db, TRACKED_REGIONS)


def start_scheduler():
    """Registers and starts all background jobs. Safe to call once at app startup."""
    if scheduler.running:
        logger.warning("Scheduler already running, skipping start.")
        return

    scheduler.add_job(_run_air_quality_job, "interval", minutes=20, id="poll_air_quality")
    scheduler.add_job(_run_weather_job, "interval", minutes=20, id="poll_weather")
    scheduler.start()
    logger.info("Background scheduler started (air quality + weather polling every 20 min).")


def shutdown_scheduler():
    """Cleanly shuts down the scheduler. Call on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler shut down.")