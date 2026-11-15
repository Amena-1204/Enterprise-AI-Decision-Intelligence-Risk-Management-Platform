from __future__ import annotations
from typing import Any, Dict, List, Optional

from backend.app.database.connection import execute_query, execute_write


class Customer:
    @staticmethod
    def get_all(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return execute_query(
            "SELECT * FROM customers ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )

    @staticmethod
    def get_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
        rows = execute_query("SELECT * FROM customers WHERE id = %s LIMIT 1", (customer_id,))
        return rows[0] if rows else None

    @staticmethod
    def create(data: Dict[str, Any]) -> int:
        return execute_write(
            """INSERT INTO customers
               (external_id, first_name, last_name, email, phone, region, country,
                segment, acquisition_channel, lifetime_value, total_orders,
                last_purchase_date, account_age_days)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                data.get("external_id"),
                data["first_name"],
                data["last_name"],
                data["email"],
                data.get("phone"),
                data.get("region"),
                data.get("country", "US"),
                data.get("segment"),
                data.get("acquisition_channel"),
                data.get("lifetime_value", 0.0),
                data.get("total_orders", 0),
                data.get("last_purchase_date"),
                data.get("account_age_days", 0),
            ),
        )

    @staticmethod
    def update(customer_id: int, data: Dict[str, Any]) -> int:
        fields = []
        values = []
        allowed = [
            "first_name", "last_name", "email", "phone", "region", "country",
            "segment", "acquisition_channel", "lifetime_value", "total_orders",
            "last_purchase_date", "account_age_days", "is_active",
        ]
        for key in allowed:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return 0
        values.append(customer_id)
        return execute_write(
            f"UPDATE customers SET {', '.join(fields)} WHERE id = %s",
            tuple(values),
        )

    @staticmethod
    def delete(customer_id: int) -> int:
        return execute_write("DELETE FROM customers WHERE id = %s", (customer_id,))

    @staticmethod
    def count() -> int:
        rows = execute_query("SELECT COUNT(*) AS cnt FROM customers WHERE is_active = 1")
        return rows[0]["cnt"] if rows else 0
