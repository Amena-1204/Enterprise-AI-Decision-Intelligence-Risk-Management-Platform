import pytest


class TestSecurityUtils:
    def test_hash_and_verify_password(self):
        from backend.app.utils.security import hash_password, verify_password
        password = "MySecurePass1"
        hashed = hash_password(password)
        assert hashed != password
        assert ":" in hashed
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        from backend.app.utils.security import hash_password, verify_password
        hashed = hash_password("CorrectPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_generate_and_decode_token(self):
        from backend.app.utils.security import generate_token, decode_token
        payload = {"user_id": 42, "role": "admin"}
        secret = "test-secret"
        token = generate_token(payload, secret, expires_in=3600)
        decoded = decode_token(token, secret)
        assert decoded is not None
        assert decoded["user_id"] == 42
        assert decoded["role"] == "admin"

    def test_expired_token_returns_none(self):
        from backend.app.utils.security import generate_token, decode_token
        token = generate_token({"user_id": 1}, "secret", expires_in=-1)
        result = decode_token(token, "secret")
        assert result is None

    def test_invalid_token_returns_none(self):
        from backend.app.utils.security import decode_token
        result = decode_token("not.a.valid.token", "secret")
        assert result is None


class TestValidators:
    def test_valid_email(self):
        from backend.app.utils.validators import validate_email
        assert validate_email("user@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True

    def test_invalid_email(self):
        from backend.app.utils.validators import validate_email
        assert validate_email("notanemail") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False

    def test_password_too_short(self):
        from backend.app.utils.validators import validate_password
        valid, msg = validate_password("Ab1")
        assert valid is False
        assert "8" in msg

    def test_password_no_uppercase(self):
        from backend.app.utils.validators import validate_password
        valid, msg = validate_password("alllower1")
        assert valid is False

    def test_password_no_digit(self):
        from backend.app.utils.validators import validate_password
        valid, msg = validate_password("NoDigitHere")
        assert valid is False

    def test_valid_password(self):
        from backend.app.utils.validators import validate_password
        valid, msg = validate_password("ValidPass1")
        assert valid is True
        assert msg == ""

    def test_required_fields_missing(self):
        from backend.app.utils.validators import validate_required_fields
        error = validate_required_fields({"a": "x"}, ["a", "b"])
        assert error is not None
        assert "b" in error

    def test_required_fields_present(self):
        from backend.app.utils.validators import validate_required_fields
        error = validate_required_fields({"a": "x", "b": "y"}, ["a", "b"])
        assert error is None

    def test_sanitize_string(self):
        from backend.app.utils.validators import sanitize_string
        result = sanitize_string("  hello world  ", max_length=5)
        assert result == "hello"


class TestDatabaseConnection:
    def test_pool_not_initialized_raises(self):
        """Verify that calling get_db before init_pool raises RuntimeError."""
        import importlib
        import backend.app.database.connection as conn_module
        original_pool = conn_module._pool
        conn_module._pool = None
        try:
            with pytest.raises(RuntimeError, match="not initialized"):
                with conn_module.get_db():
                    pass
        finally:
            conn_module._pool = original_pool
