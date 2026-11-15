from __future__ import annotations
from typing import Any, Dict, List, Optional

from backend.app.database.connection import execute_query, execute_write


class Transaction:
    @staticmethod
    def get_by_customer(customer_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        return execute_query(
            "SELECT * FROM transactions WHERE customer_id = %s ORDER BY transaction_date DESC LIMIT %s",
            (customer_id, limit),
        )

    @staticmethod
    def get_by_id(txn_id: int) -> Optional[Dict[str, Any]]:
        rows = execute_query("SELECT * FROM transactions WHERE id = %s LIMIT 1", (txn_id,))
        return rows[0] if rows else None

    @staticmethod
    def get_flagged(limit: int = 100) -> List[Dict[str, Any]]:
        return execute_query(
            "SELECT * FROM transactions WHERE is_flagged = 1 ORDER BY transaction_date DESC LIMIT %s",
            (limit,),
        )

    @staticmethod
    def total_revenue() -> float:
        rows = execute_query(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions WHERE status = 'completed'"
        )
        return float(rows[0]["total"]) if rows else 0.0
