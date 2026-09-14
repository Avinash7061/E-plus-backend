import pytest
from app.services.risk_engine import compute_risk_score, get_risk_level

def test_risk_level_boundaries():
    assert get_risk_level(24) == "low"
    assert get_risk_level(25) == "moderate"
    assert get_risk_level(49) == "moderate"
    assert get_risk_level(50) == "high"
    assert get_risk_level(74) == "high"
    assert get_risk_level(75) == "critical"
    assert get_risk_level(100) == "critical"

def test_high_heart_rate_alone():
    # HR > 120 gives +25
    result = compute_risk_score({"heart_rate": 130}, None)
    assert result["score"] == 25
    assert result["risk_level"] == "moderate"
    assert result["contributing_factors"] == {"heart_rate": 130}
    
    # HR > 150 gives +40
    result2 = compute_risk_score({"heart_rate": 160}, None)
    assert result2["score"] == 40
    assert result2["risk_level"] == "moderate"
    assert result2["contributing_factors"] == {"heart_rate": 160}

def test_spo2_below_threshold():
    # SpO2 < 92 gives +30
    result = compute_risk_score({"spo2": 90}, None)
    assert result["score"] == 30
    assert result["risk_level"] == "moderate"
    assert result["contributing_factors"] == {"spo2": 90}

def test_combined_heart_rate_and_heat_index():
    # HR > 150 (+40) and heat_index > 40 (+25) = 65
    result = compute_risk_score({"heart_rate": 160}, {"heat_index": 42})
    assert result["score"] == 65
    assert result["risk_level"] == "high"
    assert result["contributing_factors"] == {"heart_rate": 160, "heat_index": 42}

def test_missing_environmental_data():
    result = compute_risk_score({"heart_rate": 100}, None)
    assert result["score"] == 0
    assert result["risk_level"] == "low"
    assert result["contributing_factors"] == {}

def test_score_never_exceeds_100():
    # HR > 150 (+40), SpO2 < 92 (+30), heat_index > 45 (+40), aqi > 200 (+20), flood = high (+30)
    # Total = 160, should cap at 100
    biometric = {"heart_rate": 160, "spo2": 85}
    environmental = {"heat_index": 50, "aqi": 300, "flood_risk_level": "critical"}
    
    result = compute_risk_score(biometric, environmental)
    assert result["score"] == 100
    assert result["risk_level"] == "critical"
    assert "heart_rate" in result["contributing_factors"]
    assert "spo2" in result["contributing_factors"]
    assert "heat_index" in result["contributing_factors"]
    assert "aqi" in result["contributing_factors"]
    assert "flood_risk_level" in result["contributing_factors"]
