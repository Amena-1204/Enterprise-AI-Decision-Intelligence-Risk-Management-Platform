"""
Unified inference predictor.
Loads all trained models and exposes a single predict() interface.
"""
import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np

_MODELS: Dict[str, Any] = {}

_MODEL_PATHS = {
    "churn": os.path.join(os.path.dirname(__file__), "..", "models", "churn", "churn.pkl"),
    "fraud": os.path.join(os.path.dirname(__file__), "..", "models", "fraud", "fraud.pkl"),
    "sales": os.path.join(os.path.dirname(__file__), "..", "models", "sales", "sales.pkl"),
    "segmentation": os.path.join(os.path.dirname(__file__), "..", "models", "segmentation", "segmentation.pkl"),
}


def _load(name: str) -> Optional[Dict]:
    if name in _MODELS:
        return _MODELS[name]
    path = _MODEL_PATHS.get(name)
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            bundle = pickle.load(f)
        _MODELS[name] = bundle
        return bundle
    return None


def predict_churn(features: Dict[str, Any]) -> Dict[str, Any]:
    bundle = _load("churn")
    if not bundle:
        return {"error": "Churn model not trained. Run ml/training/train_churn.py"}
    model = bundle["model"]
    scaler = bundle["scaler"]
    cols = bundle["feature_names"]
    X = np.array([[float(features.get(c, 0)) for c in cols]])
    X_s = scaler.transform(X)
    prob = float(model.predict_proba(X_s)[0][1])
    pred = int(prob >= 0.5)
    top_features = _top_features(bundle, X_s)
    return {
        "prediction": "CHURN" if pred else "NO_CHURN",
        "probability": round(prob, 4),
        "risk_level": _risk_level(prob),
        "top_features": top_features,
        "model_version": bundle.get("version", "unknown"),
        "explanation": _explain_churn(prob, top_features),
    }


def predict_fraud(features: Dict[str, Any]) -> Dict[str, Any]:
    bundle = _load("fraud")
    if not bundle:
        return {"error": "Fraud model not trained. Run ml/training/train_fraud.py"}
    model = bundle["model"]
    scaler = bundle["scaler"]
    cols = bundle["feature_names"]
    X = np.array([[float(features.get(c, 0)) for c in cols]])
    X_s = scaler.transform(X)
    prob = float(model.predict_proba(X_s)[0][1])
    pred = int(prob >= 0.5)
    top_features = _top_features(bundle, X_s)
    return {
        "prediction": "FRAUD" if pred else "LEGITIMATE",
        "probability": round(prob, 4),
        "risk_level": _risk_level(prob),
        "top_features": top_features,
        "model_version": bundle.get("version", "unknown"),
        "explanation": _explain_fraud(prob, top_features),
    }


def predict_sales_forecast(features: Dict[str, Any], horizon: int = 7) -> Dict[str, Any]:
    bundle = _load("sales")
    if not bundle:
        return {"error": "Sales model not trained. Run ml/training/train_sales.py"}
    model = bundle["model"]
    scaler = bundle["scaler"]
    cols = bundle["feature_names"]
    X = np.array([[float(features.get(c, 0)) for c in cols]])
    X_s = scaler.transform(X)
    base_pred = float(model.predict(X_s)[0])
    # Simple horizon expansion using trend
    forecast = [round(base_pred * (1 + 0.01 * i), 2) for i in range(horizon)]
    return {
        "forecast": forecast,
        "horizon_days": horizon,
        "model_version": bundle.get("version", "unknown"),
    }


def predict_segment(features: Dict[str, Any]) -> Dict[str, Any]:
    bundle = _load("segmentation")
    if not bundle:
        return {"error": "Segmentation model not trained. Run ml/training/train_segmentation.py"}
    model = bundle["model"]
    scaler = bundle["scaler"]
    cols = bundle["feature_names"]
    label_map = bundle.get("label_map", {})
    X = np.array([[float(features.get(c, 0)) for c in cols]])
    X_s = scaler.transform(X)
    cluster_id = int(model.predict(X_s)[0])
    label = label_map.get(cluster_id, "Unknown")
    return {
        "cluster_id": cluster_id,
        "segment_label": label,
        "model_version": bundle.get("version", "unknown"),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _risk_level(prob: float) -> str:
    if prob >= 0.8:
        return "CRITICAL"
    if prob >= 0.6:
        return "HIGH"
    if prob >= 0.4:
        return "MEDIUM"
    return "LOW"


def _top_features(bundle: Dict, X_scaled: np.ndarray) -> List[str]:
    try:
        model = bundle["model"]
        names = bundle.get("feature_names", [])
        if hasattr(model, "feature_importances_"):
            idx = np.argsort(model.feature_importances_)[::-1][:3]
            return [names[i] for i in idx if i < len(names)]
    except Exception:
        pass
    return []


def _explain_churn(prob: float, features: List[str]) -> str:
    level = _risk_level(prob)
    feat_str = ", ".join(features) if features else "various factors"
    return (
        f"This customer has a {level} churn risk ({prob:.0%} probability). "
        f"Key contributing factors: {feat_str}."
    )


def _explain_fraud(prob: float, features: List[str]) -> str:
    level = _risk_level(prob)
    feat_str = ", ".join(features) if features else "various factors"
    return (
        f"This transaction has a {level} fraud risk ({prob:.0%} probability). "
        f"Key indicators: {feat_str}."
    )
