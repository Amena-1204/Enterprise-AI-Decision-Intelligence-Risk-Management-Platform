import hashlib
import hmac
import os
import time
from functools import wraps
from typing import Any, Dict, Optional

import jwt
from flask import current_app, g, jsonify, request

from backend.app.utils.logger import app_logger


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its stored hash."""
    try:
        salt_hex, key_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


def generate_token(payload: Dict[str, Any], secret: str, expires_in: int = 3600) -> str:
    """Generate a signed JWT token."""
    payload = payload.copy()
    payload["exp"] = int(time.time()) + expires_in
    payload["iat"] = int(time.time())
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token. Returns None on failure."""
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        app_logger.warning("JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        app_logger.warning("Invalid JWT token: %s", e)
        return None


def require_auth(f):
    """Decorator: require a valid JWT Bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        payload = decode_token(token, current_app.config["JWT_SECRET_KEY"])
        if payload is None:
            return jsonify({"error": "Invalid or expired token"}), 401
        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def require_role(*roles: str):
    """Decorator: require the authenticated user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            user_role = g.current_user.get("role", "user")
            if user_role not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
