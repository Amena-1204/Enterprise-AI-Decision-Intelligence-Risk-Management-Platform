"""
Evaluate the trained churn model.
Usage: python -m ml.evaluation.evaluate_churn
"""
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay, classification_report,
    roc_auc_score, roc_curve,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "churn", "churn.pkl")


def evaluate():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Run train_churn.py first.")
        return

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = bundle["feature_names"]
    print(f"Model: {bundle['algorithm']} | Version: {bundle['version']}")
    print(f"Stored metrics: {bundle['metrics']}")

    # Generate evaluation data
    from ml.training.train_churn import generate_synthetic_data
    df = generate_synthetic_data(500)
    feature_cols = [c for c in feature_names if c in df.columns]
    X = scaler.transform(df[feature_cols].values)
    y = df["churn"].values

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    print("\nClassification Report:")
    print(classification_report(y, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y, y_prob):.4f}")

    # Feature importance
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
        fi = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
        print("\nTop Feature Importances:")
        for name, imp in fi[:10]:
            print(f"  {name}: {imp:.4f}")

    # SHAP
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X[:100])
        print("\nSHAP mean absolute values:")
        mean_shap = np.abs(shap_vals).mean(axis=0)
        if isinstance(mean_shap, np.ndarray) and mean_shap.ndim > 1:
            mean_shap = mean_shap[1]
        for name, val in sorted(zip(feature_cols, mean_shap), key=lambda x: x[1], reverse=True):
            print(f"  {name}: {val:.4f}")
    except Exception as e:
        print(f"SHAP evaluation skipped: {e}")


if __name__ == "__main__":
    evaluate()
