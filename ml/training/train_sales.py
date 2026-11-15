"""
Train sales forecasting model.
Usage: python -m ml.training.train_sales
"""
import os
import pickle
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.preprocessing.feature_engineering import SALES_FEATURE_COLS, build_sales_features
from ml.preprocessing.validation import validate_no_inf

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "sales")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(days: int = 365) -> pd.DataFrame:
    """Generate realistic synthetic daily sales data."""
    np.random.seed(42)
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(days)]
    trend = np.linspace(10000, 18000, days)
    seasonality = 2000 * np.sin(2 * np.pi * np.arange(days) / 7)  # weekly
    monthly_season = 1500 * np.sin(2 * np.pi * np.arange(days) / 30)
    noise = np.random.normal(0, 800, days)
    revenue = trend + seasonality + monthly_season + noise
    revenue = np.clip(revenue, 1000, None)

    df = pd.DataFrame({
        "sale_date": dates,
        "revenue": revenue,
        "units_sold": (revenue / 120).astype(int),
        "orders_count": (revenue / 200).astype(int),
    })
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
            SELECT sale_date, SUM(revenue) AS revenue,
                   SUM(units_sold) AS units_sold, SUM(orders_count) AS orders_count
            FROM sales GROUP BY sale_date ORDER BY sale_date
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if len(df) < 30:
            print("Insufficient DB data, using synthetic")
            return generate_synthetic_data()
        print(f"Loaded {len(df)} rows from database")
        return df
    except Exception as e:
        print(f"DB load failed ({e}), using synthetic data")
        return generate_synthetic_data()


def train(use_mlflow: bool = True) -> dict:
    print("=" * 60)
    print("SALES FORECASTING MODEL TRAINING")
    print("=" * 60)

    df = load_data_from_db()
    df = build_sales_features(df)
    df = validate_no_inf(df)

    feature_cols = [c for c in SALES_FEATURE_COLS if c in df.columns]
    X = df[feature_cols].values
    y = df["revenue"].values

    # Time-series split (no shuffle)
    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = []

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        model.fit(X_tr, y_tr)
        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        cv_scores.append(mae)
        print(f"  Fold {fold+1} MAE: {mae:.2f}")

    # Final fit on all data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    y_pred = model.predict(X_scaled)
    metrics = {
        "mae": round(mean_absolute_error(y, y_pred), 2),
        "rmse": round(np.sqrt(mean_squared_error(y, y_pred)), 2),
        "r2": round(r2_score(y, y_pred), 4),
        "cv_mae_mean": round(float(np.mean(cv_scores)), 2),
    }
    print(f"Metrics: {metrics}")

    # MLflow
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("sales_forecasting")
            with mlflow.start_run():
                mlflow.log_params({"model": "GradientBoostingRegressor", "features": len(feature_cols)})
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(model, "sales_model")
        except Exception as e:
            print(f"MLflow skipped: {e}")

    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_cols,
        "metrics": metrics,
        "version": version,
        "algorithm": "GradientBoostingRegressor",
        "trained_at": datetime.utcnow().isoformat(),
    }
    model_path = os.path.join(MODEL_DIR, "sales.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Model saved: {model_path}")
    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
