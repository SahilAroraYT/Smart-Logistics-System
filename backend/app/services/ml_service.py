import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from app.config import settings

_model = None
_encoders: dict[str, LabelEncoder] = {}


def load_model():
    global _model, _encoders
    _model = joblib.load(settings.MODEL_PATH)
    _encoders = joblib.load(settings.ENCODER_PATH)
    return _model, _encoders


def get_model():
    if _model is None:
        load_model()
    return _model


def get_encoders():
    if not _encoders:
        load_model()
    return _encoders


def compute_features(data: dict) -> pd.DataFrame:
    df = pd.DataFrame([data])

    df["customer_risk_score"] = (1 - df["past_success_rate"]) * df["customer_cancellation_rate"] * df["customer_return_rate"]
    df["delivery_difficulty_score"] = df["distance_km"] * (df["floor_number"] * 0.5) * (1 - df["lift_available"]) * 2 * (df["package_weight"] * 0.3)
    df["agent_load_risk"] = df["agent_daily_load"] * (df["previous_failed_attempt_same_order"] * 5)
    df["cod_risk_flag"] = (df["payment_type"] == "COD").astype(int)
    df["bad_weather_flag"] = df["weather"].isin(["rain", "fog"]).astype(int)
    df["high_traffic_flag"] = (df["traffic_level"] == "high").astype(int)
    df["customer_unreachable_risk"] = (1 - df["phone_reachable"]) * (1 - df["customer_available"])
    df["building_risk_score"] = df["floor_number"] * (1 - df["lift_available"]) * df["building_type"].map({"apartment": 1.0, "gated_society": 0.8, "commercial": 0.6, "independent_house": 0.4}).fillna(0.5)
    df["cod_weather_risk"] = ((df["payment_type"] == "COD") & (df["weather"].isin(["rain", "fog"]))).astype(int)
    df["agent_fatigue_score"] = df["agent_daily_load"] / 100.0 * (1 - df["agent_success_rate"])

    feature_cols = [
        "distance_km", "delivery_zone", "time_slot", "day_of_week", "month",
        "is_weekend", "is_holiday", "location_type", "building_type", "floor_number",
        "lift_available", "payment_type", "order_value", "package_weight", "package_size",
        "weather", "traffic_level", "customer_past_orders", "past_success_rate",
        "customer_cancellation_rate", "customer_return_rate", "phone_reachable",
        "customer_available", "preferred_slot_match", "otp_required",
        "agent_experience_years", "agent_success_rate", "agent_daily_load",
        "delivery_attempts", "previous_failed_attempt_same_order",
        "customer_risk_score", "delivery_difficulty_score", "agent_load_risk",
        "cod_risk_flag", "bad_weather_flag", "high_traffic_flag",
        "customer_unreachable_risk", "building_risk_score", "cod_weather_risk",
        "agent_fatigue_score",
    ]

    df_encoded = df.copy()
    encoders = get_encoders()
    for col, le in encoders.items():
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].map({c: i for i, c in enumerate(le.classes_)})

    X = df_encoded[feature_cols].astype(np.float32)
    return X


def predict(data: dict) -> dict:
    X = compute_features(data)
    model = get_model()
    prob = float(model.predict_proba(X)[0][1])
    risk_score = prob * 100

    if risk_score <= 30:
        risk_category = "LOW"
    elif risk_score <= 70:
        risk_category = "MEDIUM"
    else:
        risk_category = "HIGH"

    features = {k: float(v) for k, v in X.iloc[0].to_dict().items()}
    explanation = []
    if features.get("customer_risk_score", 0) > 0.01:
        explanation.append({"factor": "customer_risk_score", "value": round(features["customer_risk_score"], 3), "description": "Customer reliability issue"})
    if features.get("agent_load_risk", 0) > 10:
        explanation.append({"factor": "agent_load_risk", "value": round(features["agent_load_risk"], 3), "description": "Agent overloaded"})
    if features.get("high_traffic_flag", 0) == 1:
        explanation.append({"factor": "traffic", "value": 1.0, "description": "Traffic delay risk"})
    if features.get("bad_weather_flag", 0) == 1:
        explanation.append({"factor": "weather", "value": 1.0, "description": "Weather risk"})

    if risk_score > 80:
        confidence = "high"
    elif risk_score > 50:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "probability": round(prob, 4),
        "risk_score": round(risk_score, 2),
        "risk_category": risk_category,
        "confidence": confidence,
        "explanation": explanation,
    }
