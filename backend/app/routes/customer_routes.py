from flask import Blueprint, jsonify, request

from backend.app.models.transaction import Transaction
from backend.app.services.customer_service import (
    create_customer, delete_customer, get_customer, get_customers, update_customer,
)
from backend.app.utils.security import require_auth, require_role

customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")


def _safe_int(value, default: int, min_val: int = 0, max_val: int = 500) -> int:
    try:
        return max(min_val, min(int(value), max_val))
    except (TypeError, ValueError):
        return default


@customer_bp.route("", methods=["GET"])
@require_auth
def list_customers():
    limit  = _safe_int(request.args.get("limit"),  default=100, min_val=1, max_val=500)
    offset = _safe_int(request.args.get("offset"), default=0,   min_val=0, max_val=100_000)
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
        status = 404 if "not found" in message.lower() else 400
        return jsonify({"error": message}), status
    return jsonify({"message": message}), 200


@customer_bp.route("/<int:customer_id>", methods=["DELETE"])
@require_role("admin", "analyst")
def delete(customer_id: int):
    success, message = delete_customer(customer_id)
    if not success:
        return jsonify({"error": message}), 404
    return jsonify({"message": message}), 200


@customer_bp.route("/<int:customer_id>/transactions", methods=["GET"])
@require_auth
def get_transactions(customer_id: int):
    """Return transaction history for a specific customer."""
    customer = get_customer(customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    limit = _safe_int(request.args.get("limit"), default=50, min_val=1, max_val=200)
    transactions = Transaction.get_by_customer(customer_id, limit=limit)
    return jsonify({
        "customer_id":  customer_id,
        "transactions": transactions,
        "count":        len(transactions),
    }), 200
