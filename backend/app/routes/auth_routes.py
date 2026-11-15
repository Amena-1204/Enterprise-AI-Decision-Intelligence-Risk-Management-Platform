from flask import Blueprint, jsonify, request

from backend.app.services.auth_service import login_user, register_user
from backend.app.utils.validators import validate_required_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["username", "email", "password"])
    if error:
        return jsonify({"error": error}), 400

    success, message, user_id = register_user(
        data["username"], data["email"], data["password"],
        role=data.get("role", "viewer"),
    )
    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"message": message, "user_id": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    error = validate_required_fields(data, ["email", "password"])
    if error:
        return jsonify({"error": error}), 400

    success, message, result = login_user(data["email"], data["password"])
    if not success:
        return jsonify({"error": message}), 401

    return jsonify(result), 200
