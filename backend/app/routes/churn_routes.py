from flask import Blueprint, jsonify, request

from backend.app.database.connection import execute_query
from backend.app.utils.security import require_auth

churn_bp = Blueprint("churn", __name__, url_prefix="/api/churn")


@churn_bp.route("", methods=["GET"])
@require_auth
def get_churn_overview():
    rows = execute_query(
        """SELECT cp.*, c.first_name, c.last_name, c.email, c.region, c.segment
           FROM churn_predictions cp
           JOIN customers c ON cp.customer_id = c.id
           ORDER BY cp.churn_probability DESC LIMIT 50"""
    )
    return jsonify({"churn_predictions": rows, "count": len(rows)}), 200


@churn_bp.route("/at-risk", methods=["GET"])
@require_auth
def at_risk():
    rows = execute_query(
        """SELECT cp.customer_id, c.first_name, c.last_name, c.email,
                  c.region, cp.churn_probability, cp.risk_level, cp.top_features
           FROM churn_predictions cp
           JOIN customers c ON cp.customer_id = c.id
           WHERE cp.risk_level IN ('HIGH','CRITICAL')
           ORDER BY cp.churn_probability DESC"""
    )
    return jsonify({"at_risk_customers": rows, "count": len(rows)}), 200
