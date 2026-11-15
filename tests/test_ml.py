import numpy as np
import pandas as pd
import pytest


class TestFeatureEngineering:
    def test_build_sales_features_columns(self):
        from ml.preprocessing.feature_engineering import build_sales_features, SALES_FEATURE_COLS
        from datetime import datetime, timedelta
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(60)]
        df = pd.DataFrame({
            "sale_date": dates,
            "revenue": np.random.uniform(5000, 20000, 60),
        })
        result = build_sales_features(df)
        for col in SALES_FEATURE_COLS:
            assert col in result.columns, f"Missing column: {col}"

    def test_build_fraud_features_columns(self):
        from ml.preprocessing.feature_engineering import build_fraud_features, FRAUD_FEATURE_COLS
        df = pd.DataFrame({
            "id": range(10),
            "customer_id": range(10),
            "amount": np.random.uniform(100, 5000, 10),
            "transaction_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "payment_method": ["credit_card"] * 10,
            "device_type": ["desktop"] * 10,
        })
        result = build_fraud_features(df)
        for col in FRAUD_FEATURE_COLS:
            assert col in result.columns, f"Missing column: {col}"

    def test_lag_features_no_negative(self):
        from ml.preprocessing.feature_engineering import build_sales_features
        from datetime import datetime, timedelta
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(40)]
        df = pd.DataFrame({
            "sale_date": dates,
            "revenue": [10000.0] * 40,
        })
        result = build_sales_features(df)
        assert (result["lag_7"] >= 0).all()
        assert (result["rolling_mean_7"] > 0).all()


class TestDataValidation:
    def test_check_missing(self):
        from ml.preprocessing.validation import check_missing
        df = pd.DataFrame({"a": [1, None, 3], "b": [1, 2, 3]})
        result = check_missing(df)
        assert result["a"] > 0
        assert result["b"] == 0.0

    def test_validate_target_binary_valid(self):
        from ml.preprocessing.validation import validate_target_binary
        assert validate_target_binary(pd.Series([0, 1, 0, 1])) is True

    def test_validate_target_binary_invalid(self):
        from ml.preprocessing.validation import validate_target_binary
        with pytest.raises(ValueError):
            validate_target_binary(pd.Series([0, 1, 2]))

    def test_validate_no_inf(self):
        from ml.preprocessing.validation import validate_no_inf
        df = pd.DataFrame({"a": [1.0, np.inf, -np.inf], "b": [1, 2, 3]})
        result = validate_no_inf(df)
        assert not np.isinf(result["a"]).any()

    def test_class_balance_imbalanced(self):
        from ml.preprocessing.validation import check_class_balance
        y = pd.Series([0] * 95 + [1] * 5)
        result = check_class_balance(y)
        assert result["is_imbalanced"] is True

    def test_class_balance_balanced(self):
        from ml.preprocessing.validation import check_class_balance
        y = pd.Series([0] * 50 + [1] * 50)
        result = check_class_balance(y)
        assert result["is_imbalanced"] is False


class TestCleanData:
    def test_drop_duplicates(self):
        from ml.preprocessing.clean_data import drop_duplicates
        df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
        result = drop_duplicates(df)
        assert len(result) == 2

    def test_fill_numeric_nulls(self):
        from ml.preprocessing.clean_data import fill_numeric_nulls
        df = pd.DataFrame({"a": [1.0, None, 3.0]})
        result = fill_numeric_nulls(df)
        assert result["a"].isnull().sum() == 0

    def test_fill_categorical_nulls(self):
        from ml.preprocessing.clean_data import fill_categorical_nulls
        df = pd.DataFrame({"a": ["x", None, "z"]})
        result = fill_categorical_nulls(df)
        assert result["a"].isnull().sum() == 0
        assert "unknown" in result["a"].values


class TestPredictionService:
    """Rule-based fallback logic.

    These call the ``_rule_based_*`` helpers directly: the public predict_* functions
    prefer a trained model when ml/models/*.pkl exists, which would make the assertions
    depend on model artefacts rather than the rule logic under test.
    """

    def test_rule_based_churn_high_risk(self):
        from backend.app.services.prediction_service import _rule_based_churn
        result = _rule_based_churn({
            "days_since_last_purchase": 200,
            "support_tickets": 5,
            "total_orders": 1,
            "lifetime_value": 100,
        })
        assert result["prediction"] == "CHURN"
        assert result["probability"] > 0.5
        assert result["risk_level"] in ("HIGH", "CRITICAL")

    def test_rule_based_churn_low_risk(self):
        from backend.app.services.prediction_service import _rule_based_churn
        result = _rule_based_churn({
            "days_since_last_purchase": 5,
            "support_tickets": 0,
            "total_orders": 30,
            "lifetime_value": 50000,
        })
        assert result["prediction"] == "NO_CHURN"
        assert result["risk_level"] == "LOW"

    def test_rule_based_fraud_high_risk(self):
        from backend.app.services.prediction_service import _rule_based_fraud
        result = _rule_based_fraud({
            "amount": 10000,
            "hour_of_day": 3,
            "is_foreign_country": 1,
            "is_unusual_device": 1,
            "customer_avg_amount": 200,
        })
        assert result["prediction"] == "FRAUD"
        assert result["probability"] > 0.5

    def test_rule_based_fraud_low_risk(self):
        from backend.app.services.prediction_service import _rule_based_fraud
        result = _rule_based_fraud({
            "amount": 150,
            "hour_of_day": 14,
            "is_foreign_country": 0,
            "is_unusual_device": 0,
            "customer_avg_amount": 200,
        })
        assert result["prediction"] == "LEGITIMATE"

    def test_risk_level_thresholds(self):
        from backend.app.services.prediction_service import _risk_level
        assert _risk_level(0.85) == "CRITICAL"
        assert _risk_level(0.65) == "HIGH"
        assert _risk_level(0.45) == "MEDIUM"
        assert _risk_level(0.20) == "LOW"

    def test_sales_rule_based(self):
        from backend.app.services.prediction_service import predict_sales
        result = predict_sales({"rolling_mean_7": 12000})
        assert "forecast" in result
        assert len(result["forecast"]) == 7
        assert all(v > 0 for v in result["forecast"])
