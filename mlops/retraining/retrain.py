"""
Retraining workflow.
Can be triggered manually: python -m mlops.retraining.retrain --model all
Or via the Flask API (admin only).
"""
import argparse
import sys
import os
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def retrain_churn() -> Dict[str, Any]:
    print(f"[{datetime.utcnow().isoformat()}] Retraining churn model...")
    from ml.training.train_churn import train
    return train(use_mlflow=True)


def retrain_fraud() -> Dict[str, Any]:
    print(f"[{datetime.utcnow().isoformat()}] Retraining fraud model...")
    from ml.training.train_fraud import train
    return train(use_mlflow=True)


def retrain_sales() -> Dict[str, Any]:
    print(f"[{datetime.utcnow().isoformat()}] Retraining sales model...")
    from ml.training.train_sales import train
    return train(use_mlflow=True)


def retrain_segmentation() -> Dict[str, Any]:
    print(f"[{datetime.utcnow().isoformat()}] Retraining segmentation model...")
    from ml.training.train_segmentation import train
    return train(use_mlflow=True)


def retrain_all() -> Dict[str, Any]:
    results = {}
    for name, fn in [
        ("churn", retrain_churn),
        ("fraud", retrain_fraud),
        ("sales", retrain_sales),
        ("segmentation", retrain_segmentation),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            results[name] = {"error": str(e)}
    return results


_RETRAIN_MAP = {
    "churn": retrain_churn,
    "fraud": retrain_fraud,
    "sales": retrain_sales,
    "segmentation": retrain_segmentation,
    "all": retrain_all,
}


def run(model: str = "all") -> Dict[str, Any]:
    fn = _RETRAIN_MAP.get(model)
    if fn is None:
        return {"error": f"Unknown model '{model}'. Choose from: {list(_RETRAIN_MAP.keys())}"}
    return fn()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain ML models")
    parser.add_argument(
        "--model",
        choices=list(_RETRAIN_MAP.keys()),
        default="all",
        help="Which model to retrain",
    )
    args = parser.parse_args()
    result = run(args.model)
    print(f"\nRetraining result: {result}")
