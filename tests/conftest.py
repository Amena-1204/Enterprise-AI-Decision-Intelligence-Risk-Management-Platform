import os
import pytest

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "enterprise_ai_test")
os.environ.setdefault("DB_USER", "root")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("OPENAI_API_KEY", "")


@pytest.fixture(scope="session")
def app():
    from backend.app import create_app
    from backend.app.config import TestingConfig
    application = create_app(TestingConfig())
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def auth_headers(client):
    """Register and login a test user, return auth headers."""
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass1",
        "role": "admin",
    })
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "TestPass1",
    })
    if resp.status_code == 200:
        token = resp.get_json().get("token")
        return {"Authorization": f"Bearer {token}"}
    return {}
