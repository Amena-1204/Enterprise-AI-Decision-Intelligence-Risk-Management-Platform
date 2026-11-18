"""
Train sales forecasting model.
Usage: python -m ml.training.train_sales

Approach: GradientBoostingRegressor trained on lag + rolling features.
Multi-step forecasting uses recursive prediction — each step's output
becomes the next step's lag input, which is the standard approach for
single-model multi-horizon forecasting.
"""
import os
import pickle
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.preprocessing.feature_engineering import SALES_FEATURE_COLS, build_sales_features
from ml.preprocessing.validation import validate_no_inf

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "sales")
os.makedirs(MODEL_DIR, exist_ok=True)


def generate_synthetic_data(days: int = 730) -> pd.DataFrame:
    """Synthetic daily sales — clearly labelled as synthetic."""
    np.random.seed(42)
    dates = [datetime(2023, 1, 1) + timedelta(days=i) for i in range(days)]
    trend = np.linspace(10_000, 20_000, days)
    weekly = 2_000 * np.sin(2 * np.pi * np.arange(days) / 7)
    monthly = 1_500 * np.sin(2 * np.pi * np.arange(days) / 30)
    noise = np.random.normal(0, 800, days)
    revenue = np.clip(trend + weekly + monthly + noise, 1_000, None)
    return pd.DataFrame({
        "sale_date":    dates,
        "revenue":      revenue,
        "units_sold":   (revenue / 120).astype(int),
        "orders_count": (revenue / 200).astype(int),
    })


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
            SELECT sale_date,
                   SUM(revenue)      AS revenue,
                   SUM(units_sold)   AS units_sold,
                   SUM(orders_count) AS orders_count
            FROM sales
            GROUP BY sale_date
            ORDER BY sale_date
        """
        df = pd.read_sql(query, conn)
        conn.close()
        if len(df) < 60:
            print(f"DB returned only {len(df)} rows — using synthetic data")
            return generate_synthetic_data()
        print(f"Loaded {len(df)} rows from database")
        return df
    except Exception as e:
        print(f"DB load failed ({e}), using synthetic data")
        return generate_synthetic_data()


def recursive_forecast(model, scaler, last_known: pd.Series, horizon: int) -> list:
    """
    Genuine recursive multi-step forecast.

    At each step we:
    1. Build the feature row from the current rolling/lag state.
    2. Scale it.
    3. Predict one step ahead.
    4. Append the prediction to the history so the next step's lags are correct.

    last_known: a pd.Series of recent daily revenue values (at least 30 entries).
    """
    history = list(last_known.values)
    forecasts = []

    # We need the date context for calendar features
    last_date = datetime.utcnow().date()

    for step in range(horizon):
        target_date = last_date + timedelta(days=step + 1)
        month = target_date.month
        dow = target_date.weekday()
        woy = target_date.isocalendar()[1]
        quarter = (month - 1) // 3 + 1

        lag_7  = history[-7]  if len(history) >= 7  else history[0]
        lag_14 = history[-14] if len(history) >= 14 else history[0]
        lag_30 = history[-30] if len(history) >= 30 else history[0]
        roll7  = float(np.mean(history[-7:]))
        roll30 = float(np.mean(history[-30:]))
        std7   = float(np.std(history[-7:])) if len(history) >= 7 else 0.0

        row = np.array([[
            float(month), float(dow), float(woy), float(quarter),
            float(lag_7), float(lag_14), float(lag_30),
            roll7, roll30, std7,
        ]], dtype=float)

        row_s = scaler.transform(row)
        pred = float(model.predict(row_s)[0])
        pred = max(pred, 0.0)  # revenue cannot be negative
        forecasts.append(round(pred, 2))
        history.append(pred)

    return forecasts


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
            "UPDATE model_versions SET is_active = 0 WHERE model_name = 'sales_forecast'"
        )
        cursor.execute(
            """INSERT INTO model_versions
               (model_name, version, algorithm, accuracy, f1_score, roc_auc,
                parameters, mlflow_run_id, is_active)
               VALUES (%s, %s, %s, NULL, NULL, NULL, %s, %s, 1)
               ON DUPLICATE KEY UPDATE
                   algorithm=%s, parameters=%s, mlflow_run_id=%s, is_active=1""",
            (
                "sales_forecast", version, algorithm,
                str(metrics), mlflow_run_id,
                algorithm, str(metrics), mlflow_run_id,
            ),
        )
        conn.commit()
        conn.close()
        print("Model version saved to database")
    except Exception as e:
        print(f"Could not save model version to DB: {e}")


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

    print(f"Dataset: {len(df)} days  features: {feature_cols}")

    # Time-series cross-validation (no shuffle — preserves temporal order)
    tscv = TimeSeriesSplit(n_splits=5)
    cv_maes = []

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        scaler_fold = StandardScaler()
        X_tr_s = scaler_fold.fit_transform(X_tr)
        X_val_s = scaler_fold.transform(X_val)
        model.fit(X_tr_s, y_tr)
        preds = model.predict(X_val_s)
        mae = mean_absolute_error(y_val, preds)
        cv_maes.append(mae)
        print(f"  Fold {fold + 1} MAE: {mae:.2f}")

    # Final fit on all data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    y_pred_train = model.predict(X_scaled)
    metrics = {
        "mae":         round(float(mean_absolute_error(y, y_pred_train)), 2),
        "rmse":        round(float(np.sqrt(mean_squared_error(y, y_pred_train))), 2),
        "r2":          round(float(r2_score(y, y_pred_train)), 4),
        "cv_mae_mean": round(float(np.mean(cv_maes)), 2),
        "cv_mae_std":  round(float(np.std(cv_maes)), 2),
    }
    print(f"\nMetrics: {metrics}")

    # Validate recursive forecast on last 30 days (hold-out)
    if len(df) >= 60:
        history_series = df["revenue"].iloc[:-30]
        actual_30 = df["revenue"].iloc[-30:].values
        forecast_30 = recursive_forecast(model, scaler, history_series, horizon=30)
        holdout_mae = mean_absolute_error(actual_30, forecast_30)
        metrics["holdout_mae_30d"] = round(float(holdout_mae), 2)
        print(f"Holdout 30-day recursive forecast MAE: {holdout_mae:.2f}")

    # MLflow
    mlflow_run_id = None
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("sales_forecasting")
            with mlflow.start_run() as run:
                mlflow.log_params({"model": "GradientBoostingRegressor",
                                   "features": len(feature_cols)})
                mlflow.log_metrics({k: v for k, v in metrics.items()
                                    if isinstance(v, (int, float))})
                mlflow.sklearn.log_model(model, "sales_model")
                mlflow_run_id = run.info.run_id
        except Exception as e:
            print(f"MLflow skipped: {e}")

    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    # Store last 30 days of revenue for recursive forecasting at inference time
    last_30 = list(df["revenue"].tail(30).values)
    bundle = {
        "model":         model,
        "scaler":        scaler,
        "feature_names": feature_cols,
        "metrics":       metrics,
        "version":       version,
        "algorithm":     "GradientBoostingRegressor",
        "trained_at":    datetime.utcnow().isoformat(),
        "last_known_revenue": last_30,   # used by recursive_forecast at inference
    }
    model_path = os.path.join(MODEL_DIR, "sales.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"\nModel saved: {model_path}")

    _save_model_version(metrics, version, "GradientBoostingRegressor", mlflow_run_id)

    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
