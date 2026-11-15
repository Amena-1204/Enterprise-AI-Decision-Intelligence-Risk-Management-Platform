"""
Train customer segmentation model using KMeans.
Usage: python -m ml.training.train_segmentation
"""
import os
import pickle
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "segmentation")
os.makedirs(MODEL_DIR, exist_ok=True)

SEGMENT_LABELS = {
    0: "High Value",
    1: "Loyal",
    2: "At Risk",
    3: "New Customer",
    4: "Low Engagement",
}

FEATURE_COLS = [
    "lifetime_value",
    "total_orders",
    "account_age_days",
    "days_since_last_purchase",
    "support_tickets",
    "avg_order_value",
]


def generate_synthetic_data(n: int = 500) -> pd.DataFrame:
    np.random.seed(42)
    return pd.DataFrame({
        "id": range(1, n + 1),
        "lifetime_value": np.random.exponential(15000, n),
        "total_orders": np.random.randint(0, 60, n),
        "account_age_days": np.random.randint(10, 1500, n),
        "days_since_last_purchase": np.random.randint(0, 400, n),
        "support_tickets": np.random.randint(0, 10, n),
        "avg_order_value": np.random.uniform(100, 3000, n),
    })


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
            SELECT c.id, c.lifetime_value, c.total_orders, c.account_age_days,
                   COALESCE(DATEDIFF(CURDATE(), c.last_purchase_date), 365) AS days_since_last_purchase,
                   COUNT(st.id) AS support_tickets,
                   COALESCE(c.lifetime_value / NULLIF(c.total_orders, 0), 0) AS avg_order_value
            FROM customers c
            LEFT JOIN support_tickets st ON c.id = st.customer_id
            GROUP BY c.id
        """
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"Loaded {len(df)} rows from database")
        return df
    except Exception as e:
        print(f"DB load failed ({e}), using synthetic data")
        return generate_synthetic_data()


def assign_segment_label(cluster_id: int, cluster_centers: np.ndarray) -> str:
    """
    Assign a meaningful label based on cluster center characteristics.
    Centers are in scaled space; we use relative ranking to assign labels.
    """
    n_clusters = len(cluster_centers)
    centers = cluster_centers

    # Score each cluster: high LTV + high orders = High Value
    # Use first two features (lifetime_value, total_orders) for ranking
    scores = centers[:, 0] + centers[:, 1]  # LTV + orders (scaled)
    recency = centers[:, 3]  # days_since_last_purchase (lower = better)

    ranked_by_value = np.argsort(scores)[::-1]
    ranked_by_recency = np.argsort(recency)

    label_map = {}
    assigned = set()

    # Highest value → High Value
    for c in ranked_by_value:
        if c not in assigned:
            label_map[c] = "High Value"
            assigned.add(c)
            break

    # Lowest recency (most recent) among remaining → Loyal
    for c in ranked_by_recency:
        if c not in assigned:
            label_map[c] = "Loyal"
            assigned.add(c)
            break

    # Newest accounts (lowest account_age_days) → New Customer
    age_rank = np.argsort(centers[:, 2])
    for c in age_rank:
        if c not in assigned:
            label_map[c] = "New Customer"
            assigned.add(c)
            break

    # Highest recency (most inactive) → At Risk
    for c in ranked_by_recency[::-1]:
        if c not in assigned:
            label_map[c] = "At Risk"
            assigned.add(c)
            break

    # Remaining → Low Engagement
    for c in range(n_clusters):
        if c not in assigned:
            label_map[c] = "Low Engagement"

    return label_map.get(cluster_id, "Unknown")


def train(n_clusters: int = 5, use_mlflow: bool = True) -> dict:
    print("=" * 60)
    print("CUSTOMER SEGMENTATION TRAINING")
    print("=" * 60)

    df = load_data_from_db()
    feature_cols = [c for c in FEATURE_COLS if c in df.columns]
    X = df[feature_cols].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Find optimal k using silhouette score (test 3–7 clusters)
    best_k, best_score = n_clusters, -1
    for k in range(3, min(8, len(df))):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        if len(set(labels)) > 1:
            score = silhouette_score(X_scaled, labels)
            print(f"  k={k} silhouette={score:.4f}")
            if score > best_score:
                best_score, best_k = score, k

    print(f"Best k={best_k} (silhouette={best_score:.4f})")

    model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_ids = model.fit_predict(X_scaled)

    # Build label map from cluster centers
    label_map = {
        c: assign_segment_label(c, model.cluster_centers_)
        for c in range(best_k)
    }
    print(f"Segment label map: {label_map}")

    df["cluster_id"] = cluster_ids
    df["segment_label"] = df["cluster_id"].map(label_map)

    segment_counts = df["segment_label"].value_counts().to_dict()
    print(f"Segment distribution: {segment_counts}")

    metrics = {
        "silhouette_score": round(best_score, 4),
        "n_clusters": best_k,
        "segment_distribution": segment_counts,
    }

    # MLflow
    if use_mlflow:
        try:
            import mlflow
            from dotenv import load_dotenv
            load_dotenv()
            mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
            mlflow.set_experiment("customer_segmentation")
            with mlflow.start_run():
                mlflow.log_params({"model": "KMeans", "n_clusters": best_k})
                mlflow.log_metric("silhouette_score", best_score)
                mlflow.sklearn.log_model(model, "segmentation_model")
        except Exception as e:
            print(f"MLflow skipped: {e}")

    version = f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_cols,
        "label_map": label_map,
        "metrics": metrics,
        "version": version,
        "algorithm": "KMeans",
        "trained_at": datetime.utcnow().isoformat(),
    }
    model_path = os.path.join(MODEL_DIR, "segmentation.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"Model saved: {model_path}")

    # Optionally persist segments to DB
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
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute(
                """INSERT INTO customer_segments (customer_id, segment_label, cluster_id, model_version)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE segment_label=%s, cluster_id=%s, model_version=%s""",
                (int(row["id"]), row["segment_label"], int(row["cluster_id"]), version,
                 row["segment_label"], int(row["cluster_id"]), version),
            )
        conn.commit()
        conn.close()
        print("Segments persisted to database")
    except Exception as e:
        print(f"DB persist skipped: {e}")

    return {"metrics": metrics, "version": version, "model_path": model_path}


if __name__ == "__main__":
    result = train()
    print(f"\nTraining complete: {result}")
