import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np

from backend.app.utils.logger import app_logger

_model_cache: Dict[str, Any] = {}


def _load_model(model_name: str) -> Optional[Any]:
    if model_name in _model_cache:
        return _model_cache[model_name]

    base = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "ml", "models"
    )
    path = os.path.join(base, model_name, f"{model_name}.pkl")
    if not os.path.exists(path):
        app_logger.warning("Model file not found: %s", path)
        return None

    with open(path, "rb") as f:
        model = pickle.load(f)
    _model_cache[model_name] = model
    app_logger.info("Model loaded: %s  version=%s", model_name, model.get("version", "?"))
    return model


# ── Payment risk encoding (must match feature_engineering.py) ─────────────────
_PAYMENT_RISK = {
    "credit_card": 1, "debit_card": 1, "paypal": 2,
    "bank_transfer": 1, "crypto": 4, "cash": 3,
}


def _model_feature_names(bundle: Dict, default_attr: str) -> List[str]:
    cols = bundle.get("feature_names")
    if cols:
        return list(cols)
    try:
        from ml.preprocessing import feature_engineering as fe
        return list(getattr(fe, default_attr))
    except Exception:
        return []


def _scaled_input(bundle: Dict, row: Dict[str, float], default_attr: str) -> Optional[np.ndarray]:
    cols = _model_feature_names(bundle, default_attr)
    if not cols:
        app_logger.error("No feature names found for bundle — cannot build input vector")
        return None
    X = np.array([[float(row.get(c, 0) or 0) for c in cols]], dtype=float)
    scaler = bundle.get("scaler")
    if scaler is not None:
        X = scaler.transform(X)
    return X


# ── Churn ─────────────────────────────────────────────────────────────────────

def _churn_row(f: Dict[str, Any]) -> Dict[str, float]:
    total_transactions = float(f.get("total_transactions", f.get("total_orders", 0)) or 0)
    total_spent = float(f.get("total_spent", f.get("lifetime_value", 0)) or 0)
    account_age_days = max(float(f.get("account_age_days", 0) or 0), 1.0)
    days_since = float(f.get("days_since_last_purchase", 365) or 365)
    support_tickets = float(f.get("support_tickets", 0) or 0)
    months = account_age_days / 30.0
    avg_order_value = float(f.get("avg_order_value", 0) or 0)
    if not avg_order_value and total_transactions:
        avg_order_value = total_spent / total_transactions
    return {
        "account_age_days":        account_age_days,
        "total_transactions":      total_transactions,
        "total_spent":             total_spent,
        "avg_order_value":         avg_order_value,
        "days_since_last_purchase": days_since,
        "support_tickets":         support_tickets,
        "open_tickets":            float(f.get("open_tickets", 0) or 0),
        "purchase_frequency":      total_transactions / months,
        "avg_monthly_spend":       total_spent / months,
        "is_high_ticket":          1.0 if support_tickets >= 3 else 0.0,
        "is_inactive_90d":         1.0 if days_since > 90 else 0.0,
    }


def predict_churn(features: Dict[str, Any]) -> Dict[str, Any]:
    bundle = _load_model("churn")
    if bundle:
        try:
            X = _scaled_input(bundle, _churn_row(features), "CHURN_FEATURE_COLS")
            if X is None:
                raise ValueError("Could not build feature vector")
            prob = float(bundle["model"].predict_proba(X)[0][1])
            prediction = int(prob >= 0.5)
            top_features = _get_top_features(bundle, X)
            return _churn_result(prob, prediction, top_features, bundle.get("version", "v1.0"))
        except Exception as e:
            app_logger.error("Churn model inference error: %s", e)
    return _rule_based_churn(features)


# ── Fraud ─────────────────────────────────────────────────────────────────────

def _fraud_row(f: Dict[str, Any]) -> Dict[str, float]:
    amount = float(f.get("amount", 0) or 0)
    hour = float(f.get("hour_of_day", 12) if f.get("hour_of_day") is not None else 12)
    dow = float(f.get("day_of_week", 0) or 0)
    avg_amount = float(f.get("customer_avg_amount", f.get("avg_amount", 0)) or 0)
    ratio = amount / (avg_amount + 1e-9) if avg_amount else 1.0
    device = str(f.get("device_type", "") or "").lower()
    unknown_device = 1.0 if (f.get("is_unusual_device") or device == "unknown") else 0.0
    return {
        "amount":              amount,
        "hour_of_day":         hour,
        "day_of_week":         dow,
        "is_weekend":          1.0 if dow >= 5 else 0.0,
        "is_night":            1.0 if (hour < 6 or hour > 22) else 0.0,
        "amount_vs_avg_ratio": ratio,
        "is_high_amount":      1.0 if ratio > 3 else 0.0,
        "payment_risk_score":  float(_PAYMENT_RISK.get(
            str(f.get("payment_method", "") or "").lower(), 2)),
        "is_unknown_device":   unknown_device,
    }


def predict_fraud(features: Dict[str, Any]) -> Dict[str, Any]:
    bundle = _load_model("fraud")
    if bundle:
        try:
            X = _scaled_input(bundle, _fraud_row(features), "FRAUD_FEATURE_COLS")
            if X is None:
                raise ValueError("Could not build feature vector")
            prob = float(bundle["model"].predict_proba(X)[0][1])
            prediction = int(prob >= 0.5)
            top_features = _get_top_features(bundle, X)
            return _fraud_result(prob, prediction, top_features, bundle.get("version", "v1.0"))
        except Exception as e:
            app_logger.error("Fraud model inference error: %s", e)
    return _rule_based_fraud(features)


# ── Sales ─────────────────────────────────────────────────────────────────────

def predict_sales(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genuine recursive multi-step sales forecast.
    Uses last_known_revenue stored in the model bundle (populated at training time)
    as the seed history, then recursively predicts each future step.
    """
    bundle = _load_model("sales")
    horizon = max(1, min(int(features.get("horizon", 7) or 7), 90))

    if bundle:
        try:
            from ml.training.train_sales import recursive_forecast
            import pandas as pd

            last_known = bundle.get("last_known_revenue", [])
            # Allow caller to override seed history
            if features.get("last_known_revenue"):
                last_known = list(features["last_known_revenue"])

            if len(last_known) < 7:
                raise ValueError("Insufficient history for recursive forecast")

            history_series = pd.Series(last_known)
            forecast = recursive_forecast(
                bundle["model"], bundle["scaler"], history_series, horizon=horizon
            )
            return {
                "forecast":      forecast,
                "horizon_days":  horizon,
                "model_version": bundle.get("version", "v1.0"),
                "method":        "recursive_multistep",
            }
        except Exception as e:
            app_logger.error("Sales model inference error: %s", e)

    return _rule_based_sales(features, horizon)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_top_features(bundle: Dict, X: np.ndarray) -> List[str]:
    try:
        feature_names = bundle.get("feature_names", [])
        model = bundle["model"]
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
            top_idx = np.argsort(importances)[::-1][:3]
            return [feature_names[i] for i in top_idx if i < len(feature_names)]
    except Exception:
        pass
    return []


def _risk_level(prob: float) -> str:
    if prob >= 0.8:
        return "CRITICAL"
    if prob >= 0.6:
        return "HIGH"
    if prob >= 0.4:
        return "MEDIUM"
    return "LOW"


def _churn_result(prob: float, prediction: int, features: List[str], version: str) -> Dict:
    return {
        "prediction":    "CHURN" if prediction else "NO_CHURN",
        "probability":   round(prob, 4),
        "risk_level":    _risk_level(prob),
        "top_features":  features,
        "model_version": version,
    }


def _fraud_result(prob: float, prediction: int, features: List[str], version: str) -> Dict:
    return {
        "prediction":    "FRAUD" if prediction else "LEGITIMATE",
        "probability":   round(prob, 4),
        "risk_level":    _risk_level(prob),
        "top_features":  features,
        "model_version": version,
    }


# ── Rule-based fallbacks (used when model is not loaded) ──────────────────────

def _rule_based_churn(f: Dict[str, Any]) -> Dict:
    score = 0.0
    features = []
    days = float(f.get("days_since_last_purchase", 0))
    tickets = int(f.get("support_tickets", 0))
    orders = int(f.get("total_orders", 0))

    if days > 90:
        score += 0.35
        features.append("long_inactivity")
    if tickets >= 3:
        score += 0.25
        features.append("multiple_support_tickets")
    if orders < 3:
        score += 0.20
        features.append("low_purchase_frequency")
    if float(f.get("lifetime_value", 0)) < 1000:
        score += 0.10
        features.append("low_lifetime_value")

    prob = min(score, 0.99)
    return _churn_result(prob, int(prob >= 0.5), features, "rule-based")


def _rule_based_fraud(f: Dict[str, Any]) -> Dict:
    score = 0.0
    features = []
    hour = int(f.get("hour_of_day", 12))
    amount = float(f.get("amount", 0))
    avg = float(f.get("customer_avg_amount", 100))

    if hour < 5 or hour > 23:
        score += 0.30
        features.append("unusual_hour")
    if amount > avg * 5:
        score += 0.35
        features.append("unusually_high_amount")
    if f.get("is_foreign_country"):
        score += 0.20
        features.append("foreign_country")
    if f.get("is_unusual_device"):
        score += 0.15
        features.append("unknown_device")

    prob = min(score, 0.99)
    return _fraud_result(prob, int(prob >= 0.5), features, "rule-based")


def _rule_based_sales(f: Dict[str, Any], horizon: int = 7) -> Dict:
    base = float(f.get("rolling_mean_7", 10_000))
    return {
        "forecast":      [round(base, 2)] * horizon,
        "horizon_days":  horizon,
        "model_version": "rule-based",
        "method":        "rule_based_constant",
    }
