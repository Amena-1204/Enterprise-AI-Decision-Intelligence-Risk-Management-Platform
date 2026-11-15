from flask import Blueprint, jsonify, request

from backend.app.services.customer_service import (
    create_customer, delete_customer, get_customer, get_customers, update_customer,
)
from backend.app.utils.security import require_auth, require_role

customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@customer_bp.route("", methods=["GET"])
@require_auth
def list_customers():
    limit = min(int(request.args.get("limit", 100)), 500)
    offset = int(request.args.get("offset", 0))
    customers = get_customers(limit=limit, offset=offset)
    return jsonify({"customers": customers, "count": len(customers)}), 200


@customer_bp.route("/<int:customer_id>", methods=["GET"])
@require_auth
def get_one(customer_id: int):
    customer = get_customer(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return jsonify(customer), 200


@customer_bp.route("", methods=["POST"])
@require_auth
def create():
    data = request.get_json(silent=True) or {}
    success, message, customer_id = create_customer(data)
    if not success:
        return jsonify({"error": message}), 400
    return jsonify({"message": message, "customer_id": customer_id}), 201


@customer_bp.route("/<int:customer_id>", methods=["PUT"])
@require_auth
def update(customer_id: int):
    data = request.get_json(silent=True) or {}
    success, message = update_customer(customer_id, data)
    if not success:
        return jsonify({"error": message}), 400 if "not found" not in message else 404
    return jsonify({"message": message}), 200


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@require_role("admin", "analyst")
def delete(customer_id: int):
    success, message = delete_customer(customer_id)
    if not success:
        return jsonify({"error": message}), 404
    return jsonify({"message": message}), 200
