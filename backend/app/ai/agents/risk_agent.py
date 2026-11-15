from typing import Any, Dict

from backend.app.database.connection import execute_query
from backend.app.ai.llm_service import chat_completion, build_system_prompt
from backend.app.utils.logger import app_logger


def run(query: str) -> Dict[str, Any]:
    """Risk agent: fetch churn/fraud risk data and answer the query."""
    context_parts = []
    fetched_data = {}
    q_lower = query.lower()

    if any(w in q_lower for w in ["churn", "at risk", "leaving", "cancel"]):
        rows = execute_query(
            """SELECT c.first_name, c.last_name, c.email, c.region,
                      cp.churn_probability, cp.risk_level, cp.top_features
               FROM churn_predictions cp
               JOIN customers c ON cp.customer_id = c.id
               ORDER BY cp.churn_probability DESC LIMIT 10"""
        )
        fetched_data["churn_risk"] = rows
        context_parts.append(f"Top Churn Risk Customers:\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["fraud", "suspicious", "flagged", "anomaly"]):
        rows = execute_query(
            """SELECT t.id AS transaction_id, c.first_name, c.last_name,
                      t.amount, t.country, fp.fraud_probability, fp.risk_level, fp.top_features
               FROM fraud_predictions fp
               JOIN transactions t ON fp.transaction_id = t.id
               JOIN customers c ON t.customer_id = c.id
               WHERE fp.is_fraud = 1
               ORDER BY fp.fraud_probability DESC LIMIT 10"""
        )
        fetched_data["fraud_cases"] = rows
        context_parts.append(f"Recent Fraud Cases:\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["risk", "risky", "dangerous", "high risk"]):
        churn_rows = execute_query(
            """SELECT COUNT(*) AS high_churn FROM churn_predictions
               WHERE risk_level IN ('HIGH','CRITICAL')"""
        )
        fraud_rows = execute_query(
            "SELECT COUNT(*) AS fraud_count FROM fraud_predictions WHERE is_fraud = 1"
        )
        summary = {
            "high_churn_customers": churn_rows[0]["high_churn"] if churn_rows else 0,
            "confirmed_fraud_cases": fraud_rows[0]["fraud_count"] if fraud_rows else 0,
        }
        fetched_data["risk_summary"] = summary
        context_parts.append(f"Risk Summary: {summary}")

    if not context_parts:
        # Default: show overall risk summary
        rows = execute_query(
            """SELECT risk_level, COUNT(*) AS count
               FROM churn_predictions GROUP BY risk_level ORDER BY count DESC"""
        )
        context_parts.append(f"Churn Risk Distribution:\n{_format_rows(rows)}")

    system = build_system_prompt(context_parts)
    response = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ]
    )

    return {
        "agent": "risk",
        "answer": response["content"],
        "data": fetched_data,
        "tokens_used": response["tokens_used"],
        "llm_configured": response.get("configured", True),
    }


def _format_rows(rows: list) -> str:
    if not rows:
        return "No data available."
    headers = list(rows[0].keys())
    lines = [" | ".join(headers)]
    for row in rows[:20]:
        lines.append(" | ".join(str(v) for v in row.values()))
    return "\n".join(lines)
