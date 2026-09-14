"""Background job: polls weather/hazard data for each tracked region and stores results."""

import logging
from datetime import datetime, timezone
from app.services.env_data_fetcher import fetch_weather

logger = logging.getLogger(__name__)


def poll_weather_job(db, regions: list[str]):
    """Fetches and stores weather/hazard data for each region.
    A failure in one region must never stop the others."""
    for region in regions:
        try:
            result = fetch_weather(region)
            if result is None:
                logger.warning(f"No weather data available for {region}, skipping.")
                continue

            db.table("environmental_readings").insert(
                {
                    "region": region,
                    "temperature": result["temperature"],
                    "heat_index": result["heat_index"],
                    "rainfall_mm": result["rainfall_mm"],
                    "flood_risk_level": result["flood_risk_level"],
                    "source": result["source"],
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                }
            ).execute()
            logger.info(f"Stored weather reading for {region}: heat_index={result['heat_index']}")

        except Exception as e:
            logger.error(f"Failed to poll/store weather for {region}: {e}")
            continue