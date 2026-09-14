"""Fetches environmental hazard data (air quality, weather) from external APIs.
Air quality uses OpenAQ (free tier, no key required). Weather is currently a 
stub since IMD's API requires registration we don't have yet."""

import logging
import random
import requests

logger = logging.getLogger(__name__)

OPENAQ_BASE_URL = "https://api.openaq.org/v3/locations"


def fetch_air_quality(region: str) -> dict | None:
    """Fetches the most recent AQI reading for a region from OpenAQ.
    Returns {"aqi": int, "source": "OpenAQ"} or None on any failure — 
    this must never raise since it runs unattended in a background job."""
    try:
        response = requests.get(
            OPENAQ_BASE_URL,
            params={"city": region, "limit": 1},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            logger.warning(f"No OpenAQ data found for region: {region}")
            return None

        # OpenAQ v3 nests measurements; grab the first available PM2.5-like value
        location = results[0]
        aqi_value = None
        for sensor in location.get("sensors", []):
            if sensor.get("parameter", {}).get("name") in ("pm25", "pm2_5"):
                aqi_value = sensor.get("latest", {}).get("value")
                break

        if aqi_value is None:
            logger.warning(f"No PM2.5 sensor data for region: {region}")
            return None

        return {"aqi": int(aqi_value), "source": "OpenAQ"}

    except requests.RequestException as e:
        logger.error(f"OpenAQ request failed for region {region}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching air quality for {region}: {e}")
        return None


def fetch_weather(region: str) -> dict | None:
    """STUB — IMD's real weather API requires registration we don't have yet.
    Returns realistic-looking mock data so the rest of the pipeline (risk engine, 
    alerts) can be built and tested against a stable shape now.
    
    TODO: Replace this with a real IMD API integration once registered. 
    Keep the same return shape ({"temperature", "heat_index", "rainfall_mm", 
    "flood_risk_level", "source"}) so no caller needs to change when swapped."""
    try:
        # Mock values in a plausible range for demonstration purposes
        temperature = round(random.uniform(28.0, 45.0), 1)
        heat_index = round(temperature + random.uniform(0, 6.0), 1)
        rainfall_mm = round(random.uniform(0, 50.0), 1)

        if rainfall_mm > 35:
            flood_risk_level = "high"
        elif rainfall_mm > 15:
            flood_risk_level = "moderate"
        else:
            flood_risk_level = "low"

        return {
            "temperature": temperature,
            "heat_index": heat_index,
            "rainfall_mm": rainfall_mm,
            "flood_risk_level": flood_risk_level,
            "source": "mock",
        }
    except Exception as e:
        logger.error(f"Unexpected error generating mock weather for {region}: {e}")
        return None