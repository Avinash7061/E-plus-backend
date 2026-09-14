"""Unit tests for env_data_fetcher.py — external HTTP calls are mocked."""

from unittest.mock import patch, MagicMock
import requests
from app.services import env_data_fetcher


@patch("app.services.env_data_fetcher.requests.get")
def test_fetch_air_quality_returns_none_on_network_failure(mock_get):
    mock_get.side_effect = requests.RequestException("network down")
    result = env_data_fetcher.fetch_air_quality("Jaipur")
    assert result is None


@patch("app.services.env_data_fetcher.requests.get")
def test_fetch_air_quality_returns_none_on_empty_results(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = env_data_fetcher.fetch_air_quality("NowhereCity")
    assert result is None


@patch("app.services.env_data_fetcher.requests.get")
def test_fetch_air_quality_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "sensors": [
                    {"parameter": {"name": "pm25"}, "latest": {"value": 120}}
                ]
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = env_data_fetcher.fetch_air_quality("Jaipur")
    assert result == {"aqi": 120, "source": "OpenAQ"}


def test_fetch_weather_returns_properly_shaped_dict():
    result = env_data_fetcher.fetch_weather("Jaipur")
    assert result is not None
    assert "temperature" in result
    assert "heat_index" in result
    assert "rainfall_mm" in result
    assert "flood_risk_level" in result
    assert result["flood_risk_level"] in ("low", "moderate", "high")
    assert result["source"] == "mock"


def test_fetch_weather_never_raises():
    # Should not raise even if called repeatedly
    for _ in range(5):
        result = env_data_fetcher.fetch_weather("SomeRegion")
        assert result is not None