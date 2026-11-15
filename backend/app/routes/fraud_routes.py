from flask import Blueprint, jsonify

from backend.app.database.connection import execute_query
from backend.app.utils.security import require_auth

fraud_bp = Blueprint("fraud", __name__, url_prefix="/api/fraud")


@fraud_bp.route("", methods=["GET"])
@require_auth
def get_fraud_overview():
    rows = execute_query(
        """SELECT fp.*, t.amount, t.customer_id, t.transaction_date, t.country
           FROM fraud_predictions fp
           JOIN transactions t ON fp.transaction_id = t.id
           ORDER BY fp.fraud_probability DESC LIMIT 50"""
    )
    return jsonify({"fraud_cases": rows, "count": len(rows)}), 200


@fraud_bp.route("/regional", methods=["GET"])
@require_auth
def regional_fraud():
    rows = execute_query(
        """SELECT t.country,
                  COUNT(*) AS fraud_count,
                  AVG(fp.fraud_probability) AS avg_probability
           FROM fraud_predictions fp
           JOIN transactions t ON fp.transaction_id = t.id
           WHERE fp.is_fraud = 1
           GROUP BY t.country ORDER BY fraud_count DESC"""
    )
    return jsonify({"regional_fraud": rows}), 200
