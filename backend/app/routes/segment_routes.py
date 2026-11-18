from flask import Blueprint, jsonify, request

from backend.app.database.connection import execute_query
from backend.app.utils.security import require_auth
from backend.app.utils.validators import validate_positive_number

segment_bp = Blueprint("segments", __name__, url_prefix="/api/segments")

_SEGMENT_DESCRIPTIONS = {
    "High Value":     "Top-tier customers with high lifetime value and frequent purchases.",
    "Loyal":          "Consistent buyers with strong engagement and repeat purchases.",
    "At Risk":        "Previously active customers showing signs of disengagement.",
    "New Customer":   "Recently acquired customers still in the onboarding phase.",
    "Low Engagement": "Customers with minimal activity and low purchase frequency.",
}


@segment_bp.route("", methods=["GET"])
@require_auth
def list_segments():
    """Return all customer segment assignments with descriptions."""
    rows = execute_query(
        """SELECT cs.customer_id, cs.segment_label, cs.cluster_id,
                  cs.score, cs.model_version, cs.segmented_at,
                  c.first_name, c.last_name, c.email, c.region
           FROM customer_segments cs
           JOIN customers c ON cs.customer_id = c.id
           ORDER BY cs.segment_label, cs.score DESC"""
    )
    # Attach descriptions
    for row in rows:
        row["description"] = _SEGMENT_DESCRIPTIONS.get(row["segment_label"], "")

    summary = execute_query(
        """SELECT segment_label, COUNT(*) AS count
           FROM customer_segments GROUP BY segment_label ORDER BY count DESC"""
    )
    return jsonify({"segments": rows, "count": len(rows), "summary": summary}), 200


@segment_bp.route("/predict", methods=["POST"])
@require_auth
def predict_segment():
    """
    Predict the segment for a single customer given their features.

    Expected JSON body:
    {
        "lifetime_value": 25000,
        "total_orders": 20,
        "account_age_days": 730,
        "days_since_last_purchase": 15,
        "support_tickets": 1,
        "avg_order_value": 1250
    }
    """
    data = request.get_json(silent=True) or {}

    # Validate numeric inputs
    required_fields = [
        "lifetime_value", "total_orders", "account_age_days",
        "days_since_last_purchase", "support_tickets", "avg_order_value",
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Field '{field}' is required"}), 400
        ok, msg = validate_positive_number(data[field], field)
        if not ok:
            return jsonify({"error": msg}), 400

    try:
        import os, pickle
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "ml", "models",
            "segmentation", "segmentation.pkl",
        )
        if not os.path.exists(model_path):
            return jsonify({"error": "Segmentation model not trained. Run ml/training/train_segmentation.py"}), 503

        with open(model_path, "rb") as f:
            bundle = pickle.load(f)

        import numpy as np
        feature_cols = bundle.get("feature_names", required_fields)
        X = np.array([[float(data.get(c, 0) or 0) for c in feature_cols]], dtype=float)
        X_s = bundle["scaler"].transform(X)
        cluster_id = int(bundle["model"].predict(X_s)[0])
        label_map = bundle.get("label_map", {})
        segment_label = label_map.get(cluster_id, "Unknown")

        return jsonify({
            "cluster_id":    cluster_id,
            "segment_label": segment_label,
            "description":   _SEGMENT_DESCRIPTIONS.get(segment_label, ""),
            "model_version": bundle.get("version", "v1.0"),
        }), 200

    except Exception as e:
        from backend.app.utils.logger import app_logger
        app_logger.error("Segmentation prediction error: %s", e)
        return jsonify({"error": "Segmentation prediction failed"}), 500


@segment_bp.route("/summary", methods=["GET"])
@require_auth
def segment_summary():
    """Return segment distribution counts."""
    rows = execute_query(
        """SELECT segment_label,
                  COUNT(*) AS customer_count,
                  AVG(score) AS avg_score
           FROM customer_segments
           GROUP BY segment_label
           ORDER BY customer_count DESC"""
    )
    for row in rows:
        row["description"] = _SEGMENT_DESCRIPTIONS.get(row["segment_label"], "")
    return jsonify({"segment_summary": rows}), 200
