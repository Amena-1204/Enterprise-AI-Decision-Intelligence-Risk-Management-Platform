import json
import os
import time
from typing import Any, Dict, Optional

from backend.app.ai.agents import analyst_agent, prediction_agent, report_agent, risk_agent
from backend.app.ai.rag_pipeline import retrieve, index_directory
from backend.app.database.connection import execute_write
from backend.app.utils.logger import app_logger

_documents_indexed = False


def _ensure_documents_indexed() -> None:
    """Index documents on first use if the vector store is empty."""
    global _documents_indexed
    if _documents_indexed:
        return
    try:
        from backend.app.ai.rag_pipeline import _get_store
        store = _get_store()
        if store.count() == 0:
            docs_base = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "documents"
            )
            for subdir in ["company_policies", "knowledge_base", "reports"]:
                path = os.path.join(docs_base, subdir)
                if os.path.isdir(path):
                    count = index_directory(path, category=subdir)
                    if count:
                        app_logger.info("Auto-indexed %s: %s chunks", subdir, count)
        _documents_indexed = True
    except Exception as e:
        app_logger.warning("Document auto-indexing failed: %s", e)
        _documents_indexed = True  # don't retry on every request


def _classify_intent(query: str) -> str:
    """Classify the user query into an agent category using keyword matching."""
    q = query.lower()
    risk_kw       = ["churn", "fraud", "risk", "suspicious", "at risk", "leaving",
                     "cancel", "flagged", "anomaly"]
    analyst_kw    = ["revenue", "sales", "growth", "region", "product", "how many",
                     "top", "count", "total", "best"]
    prediction_kw = ["predict", "forecast", "will", "future", "next", "probability",
                     "likelihood"]
    report_kw     = ["report", "summary", "performance", "overview", "summarize",
                     "policy", "refund", "document", "sla", "support"]

    if any(w in q for w in risk_kw):
        return "risk"
    if any(w in q for w in prediction_kw):
        return "prediction"
    if any(w in q for w in report_kw):
        return "report"
    if any(w in q for w in analyst_kw):
        return "analyst"
    return "report"


def ask(
    query: str,
    user_id: Optional[int] = None,
    features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Route query to the appropriate agent and return a structured response."""
    _ensure_documents_indexed()

    start_time = time.time()
    features = features or {}

    agent_name = _classify_intent(query)
    app_logger.info("AI query routed to agent=%s query='%s'", agent_name, query[:80])

    try:
        if agent_name == "risk":
            result = risk_agent.run(query)
        elif agent_name == "prediction":
            result = prediction_agent.run(query, features)
        elif agent_name == "analyst":
            result = analyst_agent.run(query)
        else:
            result = report_agent.run(query)
    except Exception as e:
        app_logger.error("Agent %s failed: %s", agent_name, e)
        result = {
            "agent":       agent_name,
            "answer":      (
                "I encountered an error processing your request. "
                "Please try again or contact support."
            ),
            "tokens_used": 0,
        }

    latency_ms = int((time.time() - start_time) * 1000)

    # Persist query and response to DB (non-fatal)
    try:
        query_id = execute_write(
            """INSERT INTO ai_queries (user_id, query_text, agent_used, sources_used)
               VALUES (%s, %s, %s, %s)""",
            (user_id, query, agent_name, json.dumps(result.get("sources", []))),
        )
        execute_write(
            """INSERT INTO ai_responses (query_id, response_text, tokens_used, latency_ms)
               VALUES (%s, %s, %s, %s)""",
            (query_id, result["answer"], result.get("tokens_used", 0), latency_ms),
        )
    except Exception as e:
        app_logger.warning("Could not persist AI query/response: %s", e)

    result["latency_ms"] = latency_ms
    return result


def generate_report(report_type: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Generate a structured business report by type."""
    query_map = {
        "performance": (
            "Summarize this month's overall business performance including "
            "revenue, churn rate, fraud cases, and top products."
        ),
        "churn": (
            "Provide a detailed churn risk analysis with top at-risk customers "
            "and recommended retention actions."
        ),
        "fraud": (
            "Provide a fraud analysis report including recent cases, "
            "risk patterns, and regional breakdown."
        ),
        "sales": (
            "Analyze sales trends, top products, and regional performance "
            "for the last 90 days."
        ),
    }
    query = query_map.get(report_type, f"Generate a {report_type} business report.")
    return ask(query, user_id=user_id)
