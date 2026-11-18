from flask import Blueprint, jsonify, request

from backend.app.database.connection import execute_query
from backend.app.utils.security import require_auth

sales_bp = Blueprint("sales", __name__, url_prefix="/api/sales")


def _safe_int(value, default: int, min_val: int = 1, max_val: int = 500) -> int:
    try:
        return max(min_val, min(int(value), max_val))
    except (TypeError, ValueError):
        return default


@sales_bp.route("", methods=["GET"])
@require_auth
def get_sales():
    region = request.args.get("region")
    limit = _safe_int(request.args.get("limit"), default=90, min_val=1, max_val=365)
    if region:
        rows = execute_query(
            "SELECT * FROM sales WHERE region = %s ORDER BY sale_date DESC LIMIT %s",
            (region, limit),
        )
    else:
        rows = execute_query(
            "SELECT * FROM sales ORDER BY sale_date DESC LIMIT %s", (limit,)
        )
    return jsonify({"sales": rows, "count": len(rows)}), 200


@sales_bp.route("/summary", methods=["GET"])
@require_auth
def sales_summary():
    rows = execute_query(
        """SELECT region,
                  SUM(revenue)      AS total_revenue,
                  SUM(units_sold)   AS total_units,
                  SUM(orders_count) AS total_orders
           FROM sales GROUP BY region ORDER BY total_revenue DESC"""
    )
    return jsonify({"summary": rows}), 200
