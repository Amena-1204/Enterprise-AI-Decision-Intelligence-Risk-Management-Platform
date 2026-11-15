"""
Evaluate the trained fraud detection model.
Usage: python -m ml.evaluation.evaluate_fraud
"""
import os
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fraud", "fraud.pkl")


def evaluate():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Run train_fraud.py first.")
        return

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = bundle["feature_names"]
    print(f"Model: {bundle['algorithm']} | Version: {bundle['version']}")
    print(f"Stored metrics: {bundle['metrics']}")

    from ml.training.train_fraud import generate_synthetic_data
    df = generate_synthetic_data(1000)
    feature_cols = [c for c in feature_names if c in df.columns]
    X = scaler.transform(df[feature_cols].values)
    y = df["is_fraud"].values

    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    print("\nClassification Report:")
    print(classification_report(y, y_pred))
    print(f"ROC-AUC: {roc_auc_score(y, y_prob):.4f}")
    print(f"Average Precision: {average_precision_score(y, y_prob):.4f}")

    if hasattr(model, "feature_importances_"):
        fi = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
        print("\nTop Feature Importances:")
        for name, imp in fi[:8]:
            print(f"  {name}: {imp:.4f}")


if __name__ == "__main__":
    evaluate()
