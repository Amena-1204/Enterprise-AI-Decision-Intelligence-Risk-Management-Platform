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
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.preprocessing.feature_engineering import CHURN_FEATURE_COLS
from ml.preprocessing.validation import (
    check_class_balance, validate_feature_columns,
    validate_no_inf, validate_target_binary,
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "churn")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(n: int = 2000) -> pd.DataFrame:
    """Synthetic churn training data — clearly labelled as synthetic."""
    np.random.seed(42)
    df = pd.DataFrame({
        "account_age_days":         np.random.randint(30, 1500, n),
        "total_transactions":       np.random.randint(0, 60, n),
        "total_spent":              np.random.uniform(0, 80_000, n),
        "avg_order_value":          np.random.uniform(0, 3_000, n),
        "days_since_last_purchase": np.random.randint(0, 400, n),
        "support_tickets":          np.random.randint(0, 10, n),
        "open_tickets":             np.random.randint(0, 5, n),
        "purchase_frequency":       np.random.uniform(0, 5, n),
        "avg_monthly_spend":        np.random.uniform(0, 5_000, n),
        "is_high_ticket":           np.random.randint(0, 2, n),
        "is_inactive_90d":          np.random.randint(0, 2, n),
    })
    churn_score = (
        (df["days_since_last_purchase"] > 90).astype(int) * 0.40
        + (df["support_tickets"] >= 3).astype(int) * 0.25
        + (df["total_transactions"] < 5).astype(int) * 0.20
        + (df["total_spent"] < 1_000).astype(int) * 0.15
    )
    df["churn"] = (churn_score + np.random.normal(0, 0.1, n) > 0.45).astype(int)
    print(f"[synthetic] rows={n}  churn_rate={df['churn'].mean():.2%}")
    return df


def load_data_from_db() -> pd.DataFrame:
    try:
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            database=os.environ.get("DB_NAME", "enterprise_ai"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
        )
        query = """
            SELECT c.id,
                   c.account_age_days,
                   c.total_orders                                                    AS total_transactions,
                   c.lifetime_value                                                  AS total_spent,
                   COALESCE(c.lifetime_value / NULLIF(c.total_orders, 0), 0)        AS avg_order_value,
                   DATEDIFF(CURDATE(), c.last_purchase_date)                         AS days_since_last_purchase,
                   COUNT(DISTINCT st.id)                                             AS support_tickets,
                   SUM(CASE WHEN st.status = 'open' THEN 1 ELSE 0 END)              AS open_tickets,
                   c.total_orders / GREATEST(c.account_age_days / 30, 1)            AS purchase_frequency,
                   c.lifetime_value / GREATEST(c.account_age_days / 30, 1)          AS avg_monthly_spend,
                   CASE WHEN COUNT(DISTINCT st.id) >= 3 THEN 1 ELSE 0 END           AS is_high_ticket,
                   CASE WHEN DATEDIFF(CURDATE(), c.last_purchase_date) > 90
                        THEN 1 ELSE 0 END                                            AS is_inactive_90d,
                   COALESCE(cp.prediction, 0)                                        AS churn
            FROM customers c
            LEFT JOIN support_tickets st ON c.id = st.customer_id
            LEFT JOIN churn_predictions cp ON c.id = cp.customer_id
            GROUP BY c.id
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if len(df) < 30:
            print(f"DB returned only {len(df)} rows — using synthetic data")
            return generate_synthetic_data()
        print(f"Loaded {len(df)} rows from database")
        return df
    except Exception as e:
        print(f"DB load failed ({e}), using synthetic data")
        return generate_synthetic_data()


def _save_model_version(metrics: dict, version: str, algorithm: str, mlflow_run_id: str = None) -> None:
    try:
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            database=os.environ.get("DB_NAME", "enterprise_ai"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
        )
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE model_versions SET is_active = 0 WHERE model_name = 'churn_model'"
        )
        cursor.execute(
            """INSERT INTO model_versions
               (model_name, version, algorithm, accuracy, f1_score, roc_auc,
                parameters, mlflow_run_id, is_active)
               VALUES (%s, %s, %s, %s, %s, %s, NULL, %s, 1)
               ON DUPLICATE KEY UPDATE
                   algorithm=%s, accuracy=%s, f1_score=%s, roc_auc=%s,
                   mlflow_run_id=%s, is_active=1""",
            (
                "churn_model", version, algorithm,
                metrics.get("accuracy"), metrics.get("f1"), metrics.get("roc_auc"),
                mlflow_run_id,
                algorithm, metrics.get("accuracy"), metrics.get("f1"),
                metrics.get("roc_auc"), mlflow_run_id,
            ),
        )
        conn.commit()
        conn.close()
        print("Model version saved to database")
    except Exception as e:
        print(f"Could not save model version to DB: {e}")


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

    X = df[feature_cols].values
    y = df["churn"].values
    validate_target_binary(pd.Series(y))

    balance = check_class_balance(pd.Series(y))
    print(f"Class balance: {balance}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            eval_metric="logloss", random_state=42,
        )
        model_name = "XGBClassifier"
    except ImportError:
        model = RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_leaf=5,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
        model_name = "RandomForestClassifier"

    print(f"Training {model_name}...")
    model.fit(X_train_s, y_train)

    y_pred = model.predict(X_test_s)
    y_prob = model.predict_proba(X_test_s)[:, 1]

    metrics = {
        "accuracy":  round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1":        round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc":   round(float(roc_auc_score(y_test, y_prob)), 4),
    }
    print(f"\nMetrics: {metrics}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Optional SHAP
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap.summary_plot(
            explainer.shap_values(X_test_s[:100]), X_test_s[:100],
            feature_names=feature_cols, show=False,
        )
        print("SHAP explainability computed")
    except Exception as e:
        print(f"SHAP not available: {e}")

    # MLflow
    mlflow_run_id = None
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("churn_prediction")
            with mlflow.start_run() as run:
                mlflow.log_params({"model": model_name, "features": len(feature_cols)})
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(model, "churn_model")
                mlflow_run_id = run.info.run_id
            print("MLflow run logged")
        except Exception as e:
            print(f"MLflow logging skipped: {e}")

    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    bundle = {
        "model":         model,
        "scaler":        scaler,
        "feature_names": feature_cols,
        "metrics":       metrics,
        "version":       version,
        "algorithm":     model_name,
        "trained_at":    datetime.utcnow().isoformat(),
    }
    model_path = os.path.join(MODEL_DIR, "churn.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\nModel saved: {model_path}")

    _save_model_version(metrics, version, model_name, mlflow_run_id)

    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
