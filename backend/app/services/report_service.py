from typing import Any, Dict, List

from backend.app.database.connection import execute_query
from backend.app.models.customer import Customer
from backend.app.models.prediction import ChurnPrediction, FraudPrediction
from backend.app.models.transaction import Transaction
from backend.app.utils.logger import app_logger


def get_dashboard_summary() -> Dict[str, Any]:
    total_customers = Customer.count()
    total_revenue = Transaction.total_revenue()
    churn_rate = ChurnPrediction.churn_rate()
    fraud_count = FraudPrediction.fraud_count()

    high_risk = execute_query(
        "SELECT COUNT(*) AS cnt FROM churn_predictions WHERE risk_level IN ('HIGH','CRITICAL')"
    )
    high_risk_count = int(high_risk[0]["cnt"]) if high_risk else 0

    # Sales growth: compare last 30 days vs prior 30 days
    growth_rows = execute_query(
        """SELECT
             COALESCE(SUM(CASE WHEN sale_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                               THEN revenue ELSE 0 END), 0) AS current_period,
             COALESCE(SUM(CASE WHEN sale_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 60 DAY)
                                               AND DATE_SUB(CURDATE(), INTERVAL 31 DAY)
                               THEN revenue ELSE 0 END), 0) AS prior_period
           FROM sales"""
    )
    current = float(growth_rows[0]["current_period"] or 0) if growth_rows else 0.0
    prior   = float(growth_rows[0]["prior_period"]   or 0) if growth_rows else 0.0
    sales_growth = round((current - prior) / prior * 100, 2) if prior > 0 else 0.0

    top_products = execute_query(
        """SELECT p.name,
                  SUM(s.revenue)    AS total_revenue,
                  SUM(s.units_sold) AS units
           FROM sales s
           JOIN products p ON s.product_id = p.id
           GROUP BY p.id, p.name
           ORDER BY total_revenue DESC
           LIMIT 5"""
    )

    regional = execute_query(
        """SELECT region,
                  SUM(revenue)    AS total_revenue,
                  SUM(units_sold) AS units
           FROM sales
           GROUP BY region
           ORDER BY total_revenue DESC"""
    )

    return {
        "total_customers":    total_customers,
        "total_revenue":      total_revenue,
        "churn_rate":         churn_rate,
        "fraud_count":        fraud_count,
        "high_risk_customers": high_risk_count,
        "sales_growth_pct":   sales_growth,
        "top_products": [
            {"name": r["name"], "revenue": float(r["total_revenue"] or 0), "units": int(r["units"] or 0)}
            for r in top_products
        ],
        "regional_performance": [
            {"region": r["region"], "revenue": float(r["total_revenue"] or 0), "units": int(r["units"] or 0)}
            for r in regional
        ],
    }
