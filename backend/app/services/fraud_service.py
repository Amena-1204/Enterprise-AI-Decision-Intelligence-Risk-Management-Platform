from typing import Any, Dict

from backend.app.models.prediction import FraudPrediction
from backend.app.services.prediction_service import predict_fraud
from backend.app.utils.logger import app_logger


def analyze_transaction(transaction_id: int, features: Dict[str, Any]) -> Dict[str, Any]:
    result = predict_fraud(features)
    try:
        FraudPrediction.save(
            transaction_id=transaction_id,
            probability=result["probability"],
            risk_level=result["risk_level"],
            is_fraud=1 if result["prediction"] == "FRAUD" else 0,
            top_features=result.get("top_features", []),
            model_version=result.get("model_version", "v1.0"),
        )
    except Exception as e:
        app_logger.error("Failed to persist fraud prediction: %s", e)
    return result
