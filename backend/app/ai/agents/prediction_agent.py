from typing import Any, Dict

from backend.app.services.prediction_service import predict_churn, predict_fraud, predict_sales
from backend.app.ai.llm_service import chat_completion, build_system_prompt
from backend.app.utils.logger import app_logger


def run(query: str, features: Dict[str, Any] = None) -> Dict[str, Any]:
    """Prediction agent: run ML predictions and explain results."""
    features = features or {}
    context_parts = []
    predictions = {}
    q_lower = query.lower()

    if any(w in q_lower for w in ["churn", "leaving", "cancel", "retention"]):
        result = predict_churn(features)
        predictions["churn"] = result
        context_parts.append(
            f"Churn Prediction:\n"
            f"  Prediction: {result['prediction']}\n"
            f"  Probability: {result['probability']}\n"
            f"  Risk Level: {result['risk_level']}\n"
            f"  Key Factors: {', '.join(result.get('top_features', []))}"
        )

    if any(w in q_lower for w in ["fraud", "suspicious", "transaction risk"]):
        result = predict_fraud(features)
        predictions["fraud"] = result
        context_parts.append(
            f"Fraud Prediction:\n"
            f"  Prediction: {result['prediction']}\n"
            f"  Probability: {result['probability']}\n"
            f"  Risk Level: {result['risk_level']}\n"
            f"  Key Factors: {', '.join(result.get('top_features', []))}"
        )

    if any(w in q_lower for w in ["sales forecast", "predict sales", "future revenue"]):
        result = predict_sales(features)
        predictions["sales"] = result
        context_parts.append(
            f"Sales Forecast (next 7 days): {result.get('forecast', [])}"
        )

    if not context_parts:
        context_parts.append("No specific prediction was requested. Please provide more context.")

    system = build_system_prompt(context_parts)
    response = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ]
    )

    return {
        "agent": "prediction",
        "answer": response["content"],
        "predictions": predictions,
        "tokens_used": response["tokens_used"],
        "llm_configured": response.get("configured", True),
    }
