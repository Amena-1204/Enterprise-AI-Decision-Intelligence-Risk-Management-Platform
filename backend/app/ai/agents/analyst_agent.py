from typing import Any, Dict

from backend.app.database.connection import execute_query
from backend.app.ai.llm_service import chat_completion, build_system_prompt
from backend.app.utils.logger import app_logger

# Safe read-only queries the analyst can run
_SAFE_QUERIES: Dict[str, str] = {
    "top_customers_by_revenue": """
        SELECT c.first_name, c.last_name, c.email, c.region,
               c.lifetime_value, c.total_orders, c.segment
        FROM customers c ORDER BY c.lifetime_value DESC LIMIT 10
    """,
    "revenue_by_region": """
        SELECT region, SUM(revenue) AS total_revenue, SUM(units_sold) AS units
        FROM sales GROUP BY region ORDER BY total_revenue DESC
    """,
    "monthly_revenue": """
        SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month,
               SUM(revenue) AS revenue, SUM(units_sold) AS units
        FROM sales GROUP BY month ORDER BY month DESC LIMIT 12
    """,
    "customer_segments": """
        SELECT segment_label, COUNT(*) AS count
        FROM customer_segments GROUP BY segment_label
    """,
    "top_products": """
        SELECT p.name, p.category, SUM(s.revenue) AS revenue, SUM(s.units_sold) AS units
        FROM sales s JOIN products p ON s.product_id = p.id
        GROUP BY p.id, p.name, p.category ORDER BY revenue DESC LIMIT 10
    """,
}


def run(query: str) -> Dict[str, Any]:
    """Analyst agent: fetch relevant business data and answer the query."""
    context_parts = []

    # Determine which data to fetch based on keywords
    q_lower = query.lower()
    fetched_data = {}

    if any(w in q_lower for w in ["revenue", "sales", "month", "growth"]):
        rows = execute_query(_SAFE_QUERIES["monthly_revenue"])
        fetched_data["monthly_revenue"] = rows
        context_parts.append(f"Monthly Revenue (last 12 months):\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["customer", "top", "best", "highest"]):
        rows = execute_query(_SAFE_QUERIES["top_customers_by_revenue"])
        fetched_data["top_customers"] = rows
        context_parts.append(f"Top Customers by Revenue:\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["region", "regional", "country", "area"]):
        rows = execute_query(_SAFE_QUERIES["revenue_by_region"])
        fetched_data["regional"] = rows
        context_parts.append(f"Revenue by Region:\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["product", "item", "sku"]):
        rows = execute_query(_SAFE_QUERIES["top_products"])
        fetched_data["products"] = rows
        context_parts.append(f"Top Products:\n{_format_rows(rows)}")

    if any(w in q_lower for w in ["segment", "group", "category"]):
        rows = execute_query(_SAFE_QUERIES["customer_segments"])
        fetched_data["segments"] = rows
        context_parts.append(f"Customer Segments:\n{_format_rows(rows)}")

    if not context_parts:
        # Default: fetch summary stats
        rows = execute_query(_SAFE_QUERIES["monthly_revenue"])
        context_parts.append(f"Recent Sales Data:\n{_format_rows(rows)}")

    system = build_system_prompt(context_parts)
    response = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ]
    )

    return {
        "agent": "analyst",
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
