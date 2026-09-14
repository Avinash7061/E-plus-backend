def get_risk_level(score: float) -> str:
    """Returns the risk level category based on the score."""
    if score < 25:
        return "low"
    elif score < 50:
        return "moderate"
    elif score < 75:
        return "high"
    else:
        return "critical"

def compute_risk_score(biometric: dict, environmental: dict | None) -> dict:
    """
    Rule-based risk scoring (v1, no ML).
    Returns a dict:
    {"score": float, "risk_level": str, "contributing_factors": dict}
    """
    score = 0.0
    contributing_factors = {}
    
    # Biometric rules
    heart_rate = biometric.get("heart_rate")
    if heart_rate is not None:
        if heart_rate > 150:
            score += 40  # 25 + 15
            contributing_factors["heart_rate"] = heart_rate
        elif heart_rate > 120:
            score += 25
            contributing_factors["heart_rate"] = heart_rate
            
    spo2 = biometric.get("spo2")
    if spo2 is not None:
        if spo2 < 92:
            score += 30
            contributing_factors["spo2"] = spo2
            
    # Environmental rules
    if environmental is not None:
        heat_index = environmental.get("heat_index")
        if heat_index is not None:
            if heat_index > 45:
                score += 40  # 25 + 15
                contributing_factors["heat_index"] = heat_index
            elif heat_index > 40:
                score += 25
                contributing_factors["heat_index"] = heat_index
                
        aqi = environmental.get("aqi")
        if aqi is not None:
            if aqi > 200:
                score += 20
                contributing_factors["aqi"] = aqi
                
        flood_risk_level = environmental.get("flood_risk_level")
        if flood_risk_level in ("high", "critical"):
            score += 30
            contributing_factors["flood_risk_level"] = flood_risk_level

    # Cap score at 100
    final_score = min(score, 100.0)
    
    return {
        "score": final_score,
        "risk_level": get_risk_level(final_score),
        "contributing_factors": contributing_factors
    }
