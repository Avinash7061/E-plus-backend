"""Background job: polls air quality for each tracked region and stores results."""

import logging
from datetime import datetime, timezone
from app.services.env_data_fetcher import fetch_air_quality

logger = logging.getLogger(__name__)


def poll_air_quality_job(db, regions: list[str]):
    """Fetches and stores air quality data for each region.
    A failure in one region must never stop the others."""
    for region in regions:
        try:
            result = fetch_air_quality(region)
            if result is None:
                logger.warning(f"No air quality data available for {region}, skipping.")
                continue

            db.table("environmental_readings").insert(
                {
                    "region": region,
                    "aqi": result["aqi"],
                    "source": result["source"],
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
            logger.info(f"Stored air quality reading for {region}: AQI={result['aqi']}")

        except Exception as e:
            logger.error(f"Failed to poll/store air quality for {region}: {e}")
            continue