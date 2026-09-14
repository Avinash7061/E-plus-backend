"""
EEG Feature Extraction, Random Forest Model Inference, and Composite Risk Calculation
"""
import os
import joblib
import numpy as np
from scipy.stats import skew, kurtosis

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "eeg_best_model.joblib")
if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) == 0:
    ROOT_FALLBACK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "eeg_best_model.joblib"))
    if os.path.exists(ROOT_FALLBACK):
        MODEL_PATH = ROOT_FALLBACK

_MODEL_BUNDLE = None

def get_model_bundle():
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 0:
            _MODEL_BUNDLE = joblib.load(MODEL_PATH)
        else:
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    return _MODEL_BUNDLE

def extract_features(window):
    """
    Extract 19 statistical, Hjorth, and frequency-domain features from 16 raw EEG values.
    Matches the exact training feature engineering in train_eeg_model.py.
    """
    window = np.asarray(window, dtype=float)
    feats = {}

    # 1. Statistical features
    feats["mean"] = float(np.mean(window))
    feats["std"] = float(np.std(window))
    feats["var"] = float(np.var(window))
    feats["min"] = float(np.min(window))
    feats["max"] = float(np.max(window))
    feats["ptp"] = float(np.ptp(window))
    feats["skew"] = float(skew(window))
    feats["kurtosis"] = float(kurtosis(window))
    feats["rms"] = float(np.sqrt(np.mean(window ** 2)))

    # Zero-crossing rate
    signs = np.sign(window)
    signs[signs == 0] = 1
    feats["zero_crossing_rate"] = float(np.sum(np.diff(signs) != 0) / len(window))

    # 2. Hjorth parameters
    d1 = np.diff(window)
    d2 = np.diff(d1)
    var_zero = float(np.var(window))
    var_d1 = float(np.var(d1)) if len(d1) > 0 else 0.0
    var_d2 = float(np.var(d2)) if len(d2) > 0 else 0.0

    activity = var_zero
    mobility = float(np.sqrt(var_d1 / var_zero)) if var_zero > 0 else 0.0
    mobility_d1 = float(np.sqrt(var_d2 / var_d1)) if var_d1 > 0 else 0.0
    complexity = float(mobility_d1 / mobility) if mobility > 0 else 0.0

    feats["hjorth_activity"] = activity
    feats["hjorth_mobility"] = mobility
    feats["hjorth_complexity"] = complexity

    # 3. Frequency-domain features (FFT band power)
    fft_vals = np.abs(np.fft.rfft(window))
    power = fft_vals ** 2
    n_bins = len(power)
    third = max(1, n_bins // 3)
    feats["power_low"] = float(np.sum(power[:third]))
    feats["power_mid"] = float(np.sum(power[third:2 * third]))
    feats["power_high"] = float(np.sum(power[2 * third:]))
    total_power = float(np.sum(power)) + 1e-9
    feats["power_ratio_low"] = float(feats["power_low"] / total_power)
    feats["power_ratio_high"] = float(feats["power_high"] / total_power)
    feats["spectral_entropy"] = float(-np.sum(
        (power / total_power) * np.log2((power / total_power) + 1e-12)
    ))

    return feats

CLASS_NAMES = {
    0: "Healthy",
    1: "Generalized Seizure",
    2: "Focal Seizure",
    3: "Seizure Event"
}

def predict_eeg_window(window_16_vals):
    """
    Given a list of 16 numeric EEG readings [X1..X16],
    runs the trained Random Forest model and returns predicted class and confidence.
    """
    if len(window_16_vals) != 16:
        raise ValueError(f"Expected 16 EEG values, received {len(window_16_vals)}")

    bundle = get_model_bundle()
    model = bundle["model"]
    scaler = bundle.get("scaler")
    model_name = bundle.get("model_name", "Random Forest")

    # Extract engineered features
    eng_feats = extract_features(window_16_vals)

    # Reconstruct exact feature vector in order:
    # X1..X16 + 19 engineered features
    feature_row = [float(v) for v in window_16_vals]
    ordered_eng_keys = [
        "mean", "std", "var", "min", "max", "ptp", "skew", "kurtosis", "rms",
        "zero_crossing_rate", "hjorth_activity", "hjorth_mobility", "hjorth_complexity",
        "power_low", "power_mid", "power_high", "power_ratio_low", "power_ratio_high", "spectral_entropy"
    ]
    for k in ordered_eng_keys:
        feature_row.append(eng_feats[k])

    X = np.array([feature_row])

    if model_name == "SVM (RBF)" and scaler is not None:
        X = scaler.transform(X)

    prediction = int(model.predict(X)[0])
    
    probabilities = {}
    confidence = 1.0
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        confidence = float(np.max(probs))
        for class_idx, prob in enumerate(probs):
            name = CLASS_NAMES.get(class_idx, f"Class {class_idx}")
            probabilities[name] = round(float(prob), 4)

    return {
        "class_id": prediction,
        "class_name": CLASS_NAMES.get(prediction, "Unknown"),
        "confidence": round(confidence, 4),
        "probabilities": probabilities,
        "features": eng_feats,
        "model_name": model_name
    }

def calculate_multimodal_risk(eeg_result, biometric=None, environmental=None):
    """
    Computes holistic risk score (0-100) combining:
    - EEG Seizure Model Anomaly
    - Autonomic Vitals (Heart Rate, SpO2, Skin Temp)
    - Environmental Factors (Heat Index, AQI)
    """
    score = 0.0
    contributing_factors = {}

    # 1. EEG Neurological Weight
    eeg_class = eeg_result["class_id"]
    eeg_confidence = eeg_result.get("confidence", 0.9)
    if eeg_class == 1:  # Generalized Seizure
        neurological_score = 65.0 * eeg_confidence
        score += neurological_score
        contributing_factors["neurological"] = {
            "type": "Generalized Seizure Anomaly",
            "confidence": f"{round(eeg_confidence * 100, 1)}%",
            "weight": round(neurological_score, 1)
        }
    elif eeg_class == 2:  # Focal Seizure
        neurological_score = 48.0 * eeg_confidence
        score += neurological_score
        contributing_factors["neurological"] = {
            "type": "Focal Seizure Anomaly",
            "confidence": f"{round(eeg_confidence * 100, 1)}%",
            "weight": round(neurological_score, 1)
        }
    elif eeg_class == 3:  # Seizure Event
        neurological_score = 38.0 * eeg_confidence
        score += neurological_score
        contributing_factors["neurological"] = {
            "type": "Physical Seizure Correlate",
            "confidence": f"{round(eeg_confidence * 100, 1)}%",
            "weight": round(neurological_score, 1)
        }
    else:
        contributing_factors["neurological"] = {
            "type": "Healthy Baseline Pattern",
            "confidence": f"{round(eeg_confidence * 100, 1)}%",
            "weight": 0.0
        }

    # 2. Biometric Vitals Weight
    if biometric:
        hr = biometric.get("heart_rate")
        if hr is not None:
            if hr > 140 or hr < 50:
                score += 25.0
                contributing_factors["heart_rate"] = f"Abnormal ({hr} bpm)"
            elif hr > 115:
                score += 15.0
                contributing_factors["heart_rate"] = f"Elevated ({hr} bpm)"

        spo2 = biometric.get("spo2")
        if spo2 is not None:
            if spo2 < 90:
                score += 30.0
                contributing_factors["spo2"] = f"Hypoxic ({spo2}%)"
            elif spo2 < 94:
                score += 18.0
                contributing_factors["spo2"] = f"Sub-optimal ({spo2}%)"

        temp = biometric.get("skin_temp")
        if temp is not None:
            if temp > 38.5:
                score += 20.0
                contributing_factors["skin_temp"] = f"High Fever/Strain ({temp}°C)"
            elif temp > 37.5:
                score += 10.0
                contributing_factors["skin_temp"] = f"Mild Elevation ({temp}°C)"

    # 3. Environmental Hazard Weight
    if environmental:
        heat = environmental.get("heat_index")
        if heat is not None:
            if heat > 44:
                score += 20.0
                contributing_factors["heat_index"] = f"Extreme Danger ({heat}°C)"
            elif heat > 39:
                score += 12.0
                contributing_factors["heat_index"] = f"Thermal Hazard ({heat}°C)"

        aqi = environmental.get("aqi")
        if aqi is not None:
            if aqi > 250:
                score += 15.0
                contributing_factors["aqi"] = f"Hazardous ({aqi})"
            elif aqi > 150:
                score += 8.0
                contributing_factors["aqi"] = f"Unhealthy ({aqi})"

    final_score = min(round(score, 1), 100.0)

    if final_score < 25:
        risk_level = "Low"
    elif final_score < 50:
        risk_level = "Moderate"
    elif final_score < 75:
        risk_level = "High"
    else:
        risk_level = "Critical"

    return {
        "score": final_score,
        "risk_level": risk_level,
        "contributing_factors": contributing_factors
    }

