"""Unit tests for poll_air_quality_job and poll_weather_job — fetch functions and db are mocked."""

from unittest.mock import patch, MagicMock
from app.jobs.poll_air_quality import poll_air_quality_job
from app.jobs.poll_weather import poll_weather_job


@patch("app.jobs.poll_air_quality.fetch_air_quality")
def test_air_quality_job_continues_after_one_region_fails(mock_fetch):
    mock_fetch.side_effect = [None, {"aqi": 150, "source": "OpenAQ"}]
    mock_db = MagicMock()

    poll_air_quality_job(mock_db, ["FailRegion", "GoodRegion"])

    # Only the successful region should trigger an insert
    assert mock_db.table.call_count == 1


@patch("app.jobs.poll_air_quality.fetch_air_quality")
def test_air_quality_job_inserts_on_success(mock_fetch):
    mock_fetch.return_value = {"aqi": 100, "source": "OpenAQ"}
    mock_db = MagicMock()

    poll_air_quality_job(mock_db, ["Jaipur"])

    mock_db.table.assert_called_with("environmental_readings")
    mock_db.table().insert.assert_called()


@patch("app.jobs.poll_weather.fetch_weather")
def test_weather_job_continues_after_one_region_fails(mock_fetch):
    mock_fetch.side_effect = [
        None,
        {
            "temperature": 40.0,
            "heat_index": 44.0,
            "rainfall_mm": 5.0,
            "flood_risk_level": "low",
            "source": "mock",
        },
    ]
    mock_db = MagicMock()

    poll_weather_job(mock_db, ["FailRegion", "GoodRegion"])

    assert mock_db.table.call_count == 1


@patch("app.jobs.poll_weather.fetch_weather")
def test_weather_job_inserts_on_success(mock_fetch):
    mock_fetch.return_value = {
        "temperature": 38.0,
        "heat_index": 41.0,
        "rainfall_mm": 2.0,
        "flood_risk_level": "low",
        "source": "mock",
    }
    mock_db = MagicMock()

    poll_weather_job(mock_db, ["Jaipur"])

    mock_db.table.assert_called_with("environmental_readings")
    mock_db.table().insert.assert_called()