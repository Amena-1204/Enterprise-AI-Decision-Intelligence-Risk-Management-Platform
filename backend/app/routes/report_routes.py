from flask import Blueprint, g, jsonify, request

from backend.app.services.report_service import get_dashboard_summary
from backend.app.utils.security import require_auth, require_role

report_bp = Blueprint("reports", __name__, url_prefix="/api")


@report_bp.route("/dashboard/summary", methods=["GET"])
@require_auth
def dashboard_summary():
    try:
        summary = get_dashboard_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@report_bp.route("/admin/retrain", methods=["POST"])
@require_role("admin")
def trigger_retrain():
    data = request.get_json(silent=True) or {}
    model = data.get("model", "all")
    try:
        from mlops.retraining.retrain import run
        result = run(model)
        return jsonify({"status": "completed", "result": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
