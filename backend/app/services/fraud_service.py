import json
from typing import Any, Dict

from backend.app.database.connection import execute_write
from backend.app.services.prediction_service import predict_fraud
from backend.app.utils.logger import app_logger


def analyze_transaction(transaction_id: int, features: Dict[str, Any]) -> Dict[str, Any]:
    result = predict_fraud(features)
    try:
        # Use INSERT ... ON DUPLICATE KEY UPDATE to respect the UNIQUE constraint
        # on transaction_id (added in migration 001_fix_constraints.sql).
        execute_write(
            """INSERT INTO fraud_predictions
               (transaction_id, fraud_probability, risk_level, is_fraud,
                top_features, model_version)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE
                   fraud_probability = VALUES(fraud_probability),
                   risk_level        = VALUES(risk_level),
                   is_fraud          = VALUES(is_fraud),
                   top_features      = VALUES(top_features),
                   model_version     = VALUES(model_version),
                   predicted_at      = CURRENT_TIMESTAMP""",
            (
                transaction_id,
                result["probability"],
                result["risk_level"],
                1 if result["prediction"] == "FRAUD" else 0,
                json.dumps(result.get("top_features", [])),
                result.get("model_version", "v1.0"),
            ),
        )
    except Exception as e:
        app_logger.error("Failed to persist fraud prediction: %s", e)
    return result
