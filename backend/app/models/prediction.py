from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from backend.app.database.connection import execute_query, execute_write


class ChurnPrediction:
    @staticmethod
    def save(customer_id: int, probability: float, risk_level: str,
             prediction: int, top_features: List[str], model_version: str = "v1.0") -> int:
        return execute_write(
            """INSERT INTO churn_predictions
               (customer_id, churn_probability, risk_level, prediction, top_features, model_version)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (customer_id, probability, risk_level, prediction,
             json.dumps(top_features), model_version),
        )

    @staticmethod
    def get_latest_for_customer(customer_id: int) -> Optional[Dict[str, Any]]:
        rows = execute_query(
            "SELECT * FROM churn_predictions WHERE customer_id = %s ORDER BY predicted_at DESC LIMIT 1",
            (customer_id,),
        )
        return rows[0] if rows else None

    @staticmethod
    def get_high_risk(limit: int = 50) -> List[Dict[str, Any]]:
        return execute_query(
            """SELECT cp.*, c.first_name, c.last_name, c.email, c.region
               FROM churn_predictions cp
               JOIN customers c ON cp.customer_id = c.id
               WHERE cp.risk_level IN ('HIGH','CRITICAL')
               ORDER BY cp.churn_probability DESC LIMIT %s""",
            (limit,),
        )

    @staticmethod
    def churn_rate() -> float:
        rows = execute_query(
            """SELECT
                 COUNT(*) AS total,
                 SUM(CASE WHEN prediction = 1 THEN 1 ELSE 0 END) AS churned
               FROM churn_predictions cp
               INNER JOIN (
                 SELECT customer_id, MAX(predicted_at) AS max_dt
                 FROM churn_predictions GROUP BY customer_id
               ) latest ON cp.customer_id = latest.customer_id AND cp.predicted_at = latest.max_dt"""
        )
        if rows and rows[0]["total"]:
            return round(rows[0]["churned"] / rows[0]["total"], 4)
        return 0.0


class FraudPrediction:
    @staticmethod
    def save(transaction_id: int, probability: float, risk_level: str,
             is_fraud: int, top_features: List[str], model_version: str = "v1.0") -> int:
        return execute_write(
            """INSERT INTO fraud_predictions
               (transaction_id, fraud_probability, risk_level, is_fraud, top_features, model_version)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (transaction_id, probability, risk_level, is_fraud,
             json.dumps(top_features), model_version),
        )

    @staticmethod
    def get_recent(limit: int = 50) -> List[Dict[str, Any]]:
        return execute_query(
            """SELECT fp.*, t.amount, t.customer_id, t.transaction_date
               FROM fraud_predictions fp
               JOIN transactions t ON fp.transaction_id = t.id
               ORDER BY fp.predicted_at DESC LIMIT %s""",
            (limit,),
        )

    @staticmethod
    def fraud_count() -> int:
        rows = execute_query(
            "SELECT COUNT(*) AS cnt FROM fraud_predictions WHERE is_fraud = 1"
        )
        return rows[0]["cnt"] if rows else 0
