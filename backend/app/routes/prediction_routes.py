from flask import Blueprint, jsonify, request

from backend.app.models.prediction import ChurnPrediction, FraudPrediction
from backend.app.services.churn_service import analyze_customer_churn
from backend.app.services.fraud_service import analyze_transaction
from backend.app.services.prediction_service import predict_sales
from backend.app.utils.security import require_auth

prediction_bp = Blueprint("predictions", __name__, url_prefix="/api/predictions")


# ── Churn ─────────────────────────────────────────────────────────────────────

@prediction_bp.route("/churn", methods=["GET"])
@require_auth
def get_churn():
    results = ChurnPrediction.get_high_risk(limit=50)
    return jsonify({"high_risk_customers": results, "count": len(results)}), 200


@prediction_bp.route("/churn", methods=["POST"])
@require_auth
def post_churn():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    if not customer_id:
        return jsonify({"error": "customer_id is required"}), 400
    result = analyze_customer_churn(int(customer_id), data)
    return jsonify(result), 200


# ── Fraud ─────────────────────────────────────────────────────────────────────

@prediction_bp.route("/fraud", methods=["GET"])
@require_auth
def get_fraud():
    results = FraudPrediction.get_recent(limit=50)
    return jsonify({"fraud_predictions": results, "count": len(results)}), 200


@prediction_bp.route("/fraud", methods=["POST"])
@require_auth
def post_fraud():
    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id")
    if not transaction_id:
        return jsonify({"error": "transaction_id is required"}), 400
    result = analyze_transaction(int(transaction_id), data)
    return jsonify(result), 200


# ── Sales ─────────────────────────────────────────────────────────────────────

@prediction_bp.route("/sales", methods=["GET"])
@require_auth
def get_sales():
    from backend.app.database.connection import execute_query
    rows = execute_query(
        "SELECT * FROM sales_predictions ORDER BY forecast_date DESC LIMIT 30"
    )
    return jsonify({"sales_predictions": rows}), 200


@prediction_bp.route("/sales", methods=["POST"])
@require_auth
def post_sales():
    data = request.get_json(silent=True) or {}
    result = predict_sales(data)
    return jsonify(result), 200
