from typing import Any, Dict

from backend.app.services.report_service import get_dashboard_summary
from backend.app.ai.rag_pipeline import retrieve
from backend.app.ai.llm_service import chat_completion, build_system_prompt
from backend.app.utils.logger import app_logger


def run(query: str) -> Dict[str, Any]:
    """Report agent: combine ML + DB + RAG to generate business reports."""
    context_parts = []
    sources = []

    # Always include dashboard summary for report queries
    try:
        summary = get_dashboard_summary()
        context_parts.append(
            f"Business Summary:\n"
            f"  Total Customers: {summary['total_customers']}\n"
            f"  Total Revenue: ${summary['total_revenue']:,.2f}\n"
            f"  Churn Rate: {summary['churn_rate'] * 100:.1f}%\n"
            f"  Fraud Cases: {summary['fraud_count']}\n"
            f"  High Risk Customers: {summary['high_risk_customers']}\n"
            f"  Sales Growth: {summary['sales_growth_pct']}%\n"
            f"  Top Products: {[p['name'] for p in summary.get('top_products', [])]}\n"
            f"  Regional Performance: {summary.get('regional_performance', [])}"
        )
    except Exception as e:
        app_logger.warning("Could not fetch dashboard summary: %s", e)

    # Retrieve relevant document context
    rag_results = retrieve(query, top_k=3)
    if rag_results:
        for r in rag_results:
            context_parts.append(f"[Source: {r['source']}]\n{r['text']}")
            sources.append(r["source"])

    system = build_system_prompt(context_parts)
    response = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        max_tokens=1500,
    )

    return {
        "agent": "report",
        "answer": response["content"],
        "sources": list(set(sources)),
        "tokens_used": response["tokens_used"],
        "llm_configured": response.get("configured", True),
    }
