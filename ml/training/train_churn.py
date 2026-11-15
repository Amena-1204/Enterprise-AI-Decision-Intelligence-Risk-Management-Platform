"""
Train customer churn prediction model.
Usage: python -m ml.training.train_churn
"""
import os
import pickle
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.preprocessing.feature_engineering import CHURN_FEATURE_COLS
from ml.preprocessing.validation import (
    check_class_balance, validate_feature_columns,
    validate_no_inf, validate_target_binary,
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "churn")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(n: int = 2000) -> pd.DataFrame:
    """Generate synthetic churn training data when no DB is available."""
    np.random.seed(42)
    df = pd.DataFrame({
        "account_age_days": np.random.randint(30, 1500, n),
        "total_transactions": np.random.randint(0, 60, n),
        "total_spent": np.random.uniform(0, 80000, n),
        "avg_order_value": np.random.uniform(0, 3000, n),
        "days_since_last_purchase": np.random.randint(0, 400, n),
        "support_tickets": np.random.randint(0, 10, n),
        "open_tickets": np.random.randint(0, 5, n),
        "purchase_frequency": np.random.uniform(0, 5, n),
        "avg_monthly_spend": np.random.uniform(0, 5000, n),
        "is_high_ticket": np.random.randint(0, 2, n),
        "is_inactive_90d": np.random.randint(0, 2, n),
    })
    # Realistic churn label: high inactivity + low spend + many tickets → churn
    churn_score = (
        (df["days_since_last_purchase"] > 90).astype(int) * 0.4
        + (df["support_tickets"] >= 3).astype(int) * 0.25
        + (df["total_transactions"] < 5).astype(int) * 0.2
        + (df["total_spent"] < 1000).astype(int) * 0.15
    )
    df["churn"] = (churn_score + np.random.normal(0, 0.1, n) > 0.45).astype(int)
    return df


def load_data_from_db() -> pd.DataFrame:
    """Load training data from MySQL. Falls back to synthetic data."""
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
            SELECT c.id, c.account_age_days, c.total_orders AS total_transactions,
                   c.lifetime_value AS total_spent,
                   COALESCE(c.lifetime_value / NULLIF(c.total_orders, 0), 0) AS avg_order_value,
                   DATEDIFF(CURDATE(), c.last_purchase_date) AS days_since_last_purchase,
                   COUNT(DISTINCT st.id) AS support_tickets,
                   SUM(CASE WHEN st.status = 'open' THEN 1 ELSE 0 END) AS open_tickets,
                   c.total_orders / GREATEST(c.account_age_days / 30, 1) AS purchase_frequency,
                   c.lifetime_value / GREATEST(c.account_age_days / 30, 1) AS avg_monthly_spend,
                   CASE WHEN COUNT(DISTINCT st.id) >= 3 THEN 1 ELSE 0 END AS is_high_ticket,
                   CASE WHEN DATEDIFF(CURDATE(), c.last_purchase_date) > 90 THEN 1 ELSE 0 END AS is_inactive_90d,
                   COALESCE(cp.prediction, 0) AS churn
            FROM customers c
            LEFT JOIN support_tickets st ON c.id = st.customer_id
            LEFT JOIN churn_predictions cp ON c.id = cp.customer_id
            GROUP BY c.id
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
    print("CHURN MODEL TRAINING")
    print("=" * 60)

    df = load_data_from_db()
    df = validate_no_inf(df)

    valid, missing_cols = validate_feature_columns(df, CHURN_FEATURE_COLS)
    if not valid:
        print(f"Missing columns: {missing_cols}. Using available columns.")
        feature_cols = [c for c in CHURN_FEATURE_COLS if c in df.columns]
    else:
        feature_cols = CHURN_FEATURE_COLS

    X = df[feature_cols].values
    y = df["churn"].values
    validate_target_binary(pd.Series(y))

    balance = check_class_balance(pd.Series(y))
    print(f"Class balance: {balance}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Try XGBoost first, fall back to RandomForest
    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            use_label_encoder=False, eval_metric="logloss",
            random_state=42,
        )
        model_name = "XGBClassifier"
    except ImportError:
        model = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
        model_name = "RandomForestClassifier"

    print(f"Training {model_name}...")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_prob), 4),
    }
    print(f"Metrics: {metrics}")
    print(classification_report(y_test, y_pred))

    # SHAP explainability
    shap_values = None
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test_scaled[:100])
        print("SHAP explainability computed")
    except Exception as e:
        print(f"SHAP not available: {e}")

    # MLflow tracking
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("churn_prediction")
            with mlflow.start_run():
                mlflow.log_params({"model": model_name, "features": len(feature_cols)})
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(model, "churn_model")
            print("MLflow run logged")
        except Exception as e:
            print(f"MLflow logging skipped: {e}")

    # Save model bundle
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
    model_path = os.path.join(MODEL_DIR, "churn.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Model saved: {model_path}")

    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
