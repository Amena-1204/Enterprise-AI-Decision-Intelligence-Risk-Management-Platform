import pytest
from uuid import uuid4


class TestCustomerAPI:
    def test_list_customers_requires_auth(self, client):
        resp = client.get("/api/customers")
        assert resp.status_code == 401

    def test_list_customers_with_auth(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.get("/api/customers", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "customers" in data
        assert "count" in data

    def test_create_customer_success(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        # unique email keeps this repeatable when the test DB is not reset between runs
        email = f"testcustomer+{uuid4().hex[:12]}@example.com"
        resp = client.post("/api/customers", headers=auth_headers, json={
            "first_name": "Test",
            "last_name": "Customer",
            "email": email,
            "region": "North America",
        })
        assert resp.status_code == 201
        assert "customer_id" in resp.get_json()

    def test_create_customer_missing_fields(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/customers", headers=auth_headers, json={
            "first_name": "NoEmail",
        })
        assert resp.status_code == 400

    def test_create_customer_invalid_email(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/customers", headers=auth_headers, json={
            "first_name": "Bad",
            "last_name": "Email",
            "email": "not-valid",
        })
        assert resp.status_code == 400

    def test_get_nonexistent_customer(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.get("/api/customers/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_pagination(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.get("/api/customers?limit=5&offset=0", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["customers"]) <= 5


class TestPredictionAPI:
    def test_churn_get(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.get("/api/predictions/churn", headers=auth_headers)
        assert resp.status_code == 200
        assert "high_risk_customers" in resp.get_json()

    def test_churn_post_success(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/predictions/churn", headers=auth_headers, json={
            "customer_id": 1,
            "days_since_last_purchase": 120,
            "total_orders": 2,
            "lifetime_value": 500,
            "support_tickets": 4,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "prediction" in data
        assert "probability" in data
        assert "risk_level" in data

    def test_churn_post_missing_customer_id(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/predictions/churn", headers=auth_headers, json={
            "days_since_last_purchase": 100,
        })
        assert resp.status_code == 400

    def test_fraud_post_success(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/predictions/fraud", headers=auth_headers, json={
            "transaction_id": 1,
            "amount": 5000,
            "hour_of_day": 3,
            "is_foreign_country": 1,
            "is_unusual_device": 1,
            "customer_avg_amount": 200,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "prediction" in data
        assert data["prediction"] in ("FRAUD", "LEGITIMATE")

    def test_sales_post(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/predictions/sales", headers=auth_headers, json={
            "month": 12,
            "rolling_mean_7": 15000,
        })
        assert resp.status_code == 200
        assert "forecast" in resp.get_json()


class TestDashboardAPI:
    def test_dashboard_summary(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.get("/api/dashboard/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        expected_keys = [
            "total_customers", "total_revenue", "churn_rate",
            "fraud_count", "high_risk_customers", "sales_growth_pct",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"


class TestAIAPI:
    def test_ask_requires_auth(self, client):
        resp = client.post("/api/ai/ask", json={"query": "test"})
        assert resp.status_code == 401

    def test_ask_missing_query(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/ai/ask", headers=auth_headers, json={})
        assert resp.status_code == 400

    def test_ask_query_too_long(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/ai/ask", headers=auth_headers, json={
            "query": "x" * 2001
        })
        assert resp.status_code == 400

    def test_ask_valid_query(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/ai/ask", headers=auth_headers, json={
            "query": "Which customers have the highest churn risk?"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "answer" in data
        assert "agent" in data

    def test_report_invalid_type(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/ai/report", headers=auth_headers, json={
            "report_type": "invalid_type"
        })
        assert resp.status_code == 400

    def test_report_valid_type(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("DB not connected")
        resp = client.post("/api/ai/report", headers=auth_headers, json={
            "report_type": "performance"
        })
        assert resp.status_code == 200
        assert "answer" in resp.get_json()


class TestHealthCheck:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
