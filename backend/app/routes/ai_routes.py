from flask import Blueprint, g, jsonify, request

from backend.app.services.ai_orchestration import ask, generate_report
from backend.app.utils.security import require_auth
from backend.app.utils.validators import validate_required_fields

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.route("/ask", methods=["POST"])
@require_auth
def ask_ai():
    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["query"])
    if error:
        return jsonify({"error": error}), 400

    query = str(data["query"]).strip()
    if len(query) > 2000:
        return jsonify({"error": "Query too long (max 2000 characters)"}), 400

    user_id = g.current_user.get("user_id")
    features = data.get("features", {})

    result = ask(query, user_id=user_id, features=features)
    return jsonify(result), 200


@ai_bp.route("/report", methods=["POST"])
@require_auth
def generate_ai_report():
    data = request.get_json(silent=True) or {}
    report_type = data.get("report_type", "performance")
    allowed_types = {"performance", "churn", "fraud", "sales"}
    if report_type not in allowed_types:
        return jsonify({"error": f"report_type must be one of: {allowed_types}"}), 400

    user_id = g.current_user.get("user_id")
    result = generate_report(report_type, user_id=user_id)
    return jsonify(result), 200


@ai_bp.route("/index-documents", methods=["POST"])
@require_auth
def index_documents():
    """Index documents from the documents directory into the vector store."""
    from backend.app.ai.rag_pipeline import index_directory
    import os

    docs_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "documents"
    )
    results = {}
    for subdir in ["company_policies", "knowledge_base", "reports"]:
        path = os.path.join(docs_dir, subdir)
        if os.path.isdir(path):
            indexed = index_directory(path, category=subdir)
            results[subdir] = indexed

    return jsonify({"indexed": results}), 200
