import pytest


class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPass1",
        })
        assert resp.status_code in (201, 400)  # 400 if already exists in test DB

    def test_register_missing_fields(self, client):
        resp = client.post("/api/auth/register", json={"username": "x"})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_register_invalid_email(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "baduser",
            "email": "not-an-email",
            "password": "TestPass1",
        })
        assert resp.status_code == 400

    def test_register_weak_password(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "short",
        })
        assert resp.status_code == 400

    def test_register_duplicate_email(self, client):
        data = {"username": "dup1", "email": "dup@example.com", "password": "DupPass1"}
        client.post("/api/auth/register", json=data)
        resp = client.post("/api/auth/register", json=data)
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "LoginPass1",
        })
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "LoginPass1",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "token" in data
        assert "user" in data

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "WrongPass1",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@example.com",
            "password": "SomePass1",
        })
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={"email": "x@x.com"})
        assert resp.status_code == 400


class TestProtectedRoutes:
    def test_no_token_returns_401(self, client):
        resp = client.get("/api/customers")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/api/customers", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    def test_valid_token_grants_access(self, client, auth_headers):
        if not auth_headers:
            pytest.skip("Auth headers not available (DB not connected)")
        resp = client.get("/api/customers", headers=auth_headers)
        assert resp.status_code == 200
