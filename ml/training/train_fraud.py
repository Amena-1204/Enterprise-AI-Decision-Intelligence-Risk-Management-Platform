"""
Train fraud detection model.
Usage: python -m ml.training.train_fraud
"""
import os
import pickle
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.preprocessing.feature_engineering import FRAUD_FEATURE_COLS
from ml.preprocessing.validation import validate_no_inf, validate_target_binary

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "fraud")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(n: int = 5000) -> pd.DataFrame:
    np.random.seed(42)
    df = pd.DataFrame({
        "amount": np.random.exponential(500, n),
        "hour_of_day": np.random.randint(0, 24, n),
        "day_of_week": np.random.randint(0, 7, n),
        "is_weekend": np.random.randint(0, 2, n),
        "is_night": np.random.randint(0, 2, n),
        "amount_vs_avg_ratio": np.random.exponential(1.2, n),
        "is_high_amount": np.random.randint(0, 2, n),
        "payment_risk_score": np.random.choice([1, 2, 3, 4], n, p=[0.5, 0.3, 0.1, 0.1]),
        "is_unknown_device": np.random.randint(0, 2, n),
    })
    # Fraud label: night + high amount + unknown device + crypto → fraud
    fraud_score = (
        df["is_night"] * 0.30
        + df["is_high_amount"] * 0.30
        + df["is_unknown_device"] * 0.20
        + (df["payment_risk_score"] >= 4).astype(int) * 0.20
    )
    df["is_fraud"] = (fraud_score + np.random.normal(0, 0.08, n) > 0.45).astype(int)
    # Realistic imbalance: ~5% fraud
    fraud_idx = df[df["is_fraud"] == 1].index
    keep = np.random.choice(fraud_idx, size=int(n * 0.05), replace=False)
    df.loc[fraud_idx, "is_fraud"] = 0
    df.loc[keep, "is_fraud"] = 1
    return df


def load_data_from_db() -> pd.DataFrame:
    try:
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            database=os.environ.get("DB_NAME", "enterprise_ai"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
        )
        query = """
            SELECT t.id, t.amount,
                   HOUR(t.transaction_date) AS hour_of_day,
                   DAYOFWEEK(t.transaction_date) - 1 AS day_of_week,
                   CASE WHEN DAYOFWEEK(t.transaction_date) IN (1,7) THEN 1 ELSE 0 END AS is_weekend,
                   CASE WHEN HOUR(t.transaction_date) < 6 OR HOUR(t.transaction_date) > 22 THEN 1 ELSE 0 END AS is_night,
                   t.amount / GREATEST(AVG(t2.amount) OVER (PARTITION BY t.customer_id), 1) AS amount_vs_avg_ratio,
                   CASE WHEN t.amount > 3000 THEN 1 ELSE 0 END AS is_high_amount,
                   CASE t.payment_method
                       WHEN 'crypto' THEN 4 WHEN 'cash' THEN 3
                       WHEN 'paypal' THEN 2 ELSE 1 END AS payment_risk_score,
                   CASE WHEN t.device_type = 'unknown' THEN 1 ELSE 0 END AS is_unknown_device,
                   COALESCE(fp.is_fraud, t.is_flagged) AS is_fraud
            FROM transactions t
            LEFT JOIN fraud_predictions fp ON t.id = fp.transaction_id
        """
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"Loaded {len(df)} rows from database")
        return df
    except Exception as e:
        print(f"DB load failed ({e}), using synthetic data")
        return generate_synthetic_data()


def train(use_mlflow: bool = True) -> dict:
    print("=" * 60)
    print("FRAUD DETECTION MODEL TRAINING")
    print("=" * 60)

    df = load_data_from_db()
    df = validate_no_inf(df)

    feature_cols = [c for c in FRAUD_FEATURE_COLS if c in df.columns]
    X = df[feature_cols].values
    y = df["is_fraud"].values
    validate_target_binary(pd.Series(y))

    print(f"Fraud rate: {y.mean():.2%}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    try:
        from xgboost import XGBClassifier
        scale_pos = int((y == 0).sum() / max((y == 1).sum(), 1))
        model = XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            scale_pos_weight=scale_pos, subsample=0.8,
            use_label_encoder=False, eval_metric="aucpr",
            random_state=42,
        )
        model_name = "XGBClassifier"
    except ImportError:
        model = RandomForestClassifier(
            n_estimators=300, max_depth=12, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )
        model_name = "RandomForestClassifier"

    print(f"Training {model_name}...")
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
    }
    print(f"Metrics: {metrics}")
    print(classification_report(y_test, y_pred))

    # SHAP
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap.summary_plot(
            explainer.shap_values(X_test_s[:200]), X_test_s[:200],
            feature_names=feature_cols, show=False,
        )
        print("SHAP computed")
    except Exception as e:
        print(f"SHAP skipped: {e}")

    # MLflow
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("fraud_detection")
            with mlflow.start_run():
                mlflow.log_params({"model": model_name, "features": len(feature_cols)})
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(model, "fraud_model")
        except Exception as e:
            print(f"MLflow skipped: {e}")

    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_cols,
        "metrics": metrics,
        "version": version,
        "algorithm": model_name,
        "trained_at": datetime.utcnow().isoformat(),
    }
    model_path = os.path.join(MODEL_DIR, "fraud.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Model saved: {model_path}")
    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
