from typing import Any, Dict

from backend.app.models.prediction import ChurnPrediction
from backend.app.services.prediction_service import predict_churn
from backend.app.utils.logger import app_logger


def analyze_customer_churn(customer_id: int, features: Dict[str, Any]) -> Dict[str, Any]:
    result = predict_churn(features)
    try:
        ChurnPrediction.save(
            customer_id=customer_id,
            probability=result["probability"],
            risk_level=result["risk_level"],
            prediction=1 if result["prediction"] == "CHURN" else 0,
            top_features=result.get("top_features", []),
            model_version=result.get("model_version", "v1.0"),
        )
    except Exception as e:
        app_logger.error("Failed to persist churn prediction: %s", e)
    return result
