"""
Model monitoring utilities.
Tracks prediction distributions and detects data/concept drift.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np


MONITORING_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(MONITORING_DIR, exist_ok=True)


def log_prediction(model_name: str, features: Dict[str, Any], prediction: Dict[str, Any]) -> None:
    """Append a prediction record to the monitoring log."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "model": model_name,
        "features": features,
        "prediction": prediction,
    }
    log_path = os.path.join(MONITORING_DIR, f"{model_name}_predictions.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_recent_predictions(model_name: str, days: int = 7) -> List[Dict]:
    """Load prediction logs from the last N days."""
    log_path = os.path.join(MONITORING_DIR, f"{model_name}_predictions.jsonl")
    if not os.path.exists(log_path):
        return []
    cutoff = datetime.utcnow() - timedelta(days=days)
    records = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                ts = datetime.fromisoformat(rec["timestamp"])
                if ts >= cutoff:
                    records.append(rec)
            except Exception:
                continue
    return records


def compute_drift_report(model_name: str, reference_probs: List[float], days: int = 7) -> Dict:
    """
    Compare recent prediction probability distribution against a reference.
    Uses Population Stability Index (PSI) as drift metric.
    """
    recent = load_recent_predictions(model_name, days=days)
    if not recent:
        return {"status": "no_data", "psi": None}

    recent_probs = []
    for r in recent:
        prob = r.get("prediction", {}).get("probability")
        if prob is not None:
            recent_probs.append(float(prob))

    if len(recent_probs) < 10:
        return {"status": "insufficient_data", "count": len(recent_probs)}

    psi = _compute_psi(reference_probs, recent_probs)
    status = "stable" if psi < 0.1 else ("warning" if psi < 0.2 else "drift_detected")

    return {
        "model": model_name,
        "status": status,
        "psi": round(psi, 4),
        "recent_mean_prob": round(float(np.mean(recent_probs)), 4),
        "reference_mean_prob": round(float(np.mean(reference_probs)), 4),
        "recent_count": len(recent_probs),
        "period_days": days,
    }


def _compute_psi(expected: List[float], actual: List[float], bins: int = 10) -> float:
    """Population Stability Index."""
    breakpoints = np.linspace(0, 1, bins + 1)
    exp_counts, _ = np.histogram(expected, bins=breakpoints)
    act_counts, _ = np.histogram(actual, bins=breakpoints)

    exp_pct = (exp_counts + 1e-6) / len(expected)
    act_pct = (act_counts + 1e-6) / len(actual)

    psi = np.sum((act_pct - exp_pct) * np.log(act_pct / exp_pct))
    return float(psi)
