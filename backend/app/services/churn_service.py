from typing import Any, Dict

from backend.app.models.prediction import ChurnPrediction
from backend.app.models.audit_log import write_audit_log
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
        write_audit_log(
            action="churn_prediction",
            resource="customers",
            resource_id=str(customer_id),
            details={
                "prediction":  result["prediction"],
                "probability": result["probability"],
                "risk_level":  result["risk_level"],
            },
        )
    except Exception as e:
        app_logger.error("Failed to persist churn prediction: %s", e)
    return result
