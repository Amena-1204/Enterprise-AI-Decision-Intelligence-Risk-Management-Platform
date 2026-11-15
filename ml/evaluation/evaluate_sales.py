"""
Evaluate the trained sales forecasting model.
Usage: python -m ml.evaluation.evaluate_sales
"""
import os
import pickle
import sys

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "sales", "sales.pkl")


def evaluate():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Run train_sales.py first.")
        return

    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_names = bundle["feature_names"]
    print(f"Model: {bundle['algorithm']} | Version: {bundle['version']}")
    print(f"Stored metrics: {bundle['metrics']}")

    from ml.training.train_sales import generate_synthetic_data
    from ml.preprocessing.feature_engineering import build_sales_features
    df = generate_synthetic_data(180)
    df = build_sales_features(df)
    feature_cols = [c for c in feature_names if c in df.columns]
    X = scaler.transform(df[feature_cols].values)
    y = df["revenue"].values

    y_pred = model.predict(X)
    print(f"\nMAE:  {mean_absolute_error(y, y_pred):.2f}")
    print(f"RMSE: {np.sqrt(mean_squared_error(y, y_pred)):.2f}")
    print(f"R²:   {r2_score(y, y_pred):.4f}")

    if hasattr(model, "feature_importances_"):
        fi = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
        print("\nTop Feature Importances:")
        for name, imp in fi[:8]:
            print(f"  {name}: {imp:.4f}")


if __name__ == "__main__":
    evaluate()
