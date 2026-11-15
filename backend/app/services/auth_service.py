from typing import Dict, Optional, Tuple

from flask import current_app

from backend.app.models.user import User
from backend.app.utils.security import generate_token, hash_password, verify_password
from backend.app.utils.validators import validate_email, validate_password
from backend.app.utils.logger import app_logger


def register_user(username: str, email: str, password: str, role: str = "viewer") -> Tuple[bool, str, Optional[int]]:
    if not validate_email(email):
        return False, "Invalid email address", None

    valid, msg = validate_password(password)
    if not valid:
        return False, msg, None

    if User.find_by_email(email):
        return False, "Email already registered", None

    hashed = hash_password(password)
    user_id = User.create(username, email, hashed, role)
    app_logger.info("New user registered: %s (id=%s)", email, user_id)
    return True, "User registered successfully", user_id


def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    user = User.find_by_email(email)
    if not user:
        return False, "Invalid credentials", None

    if not user.get("is_active"):
        return False, "Account is disabled", None

    if not verify_password(password, user["password_hash"]):
        app_logger.warning("Failed login attempt for: %s", email)
        return False, "Invalid credentials", None

    token = generate_token(
        {"user_id": user["id"], "email": user["email"], "role": user["role"]},
        current_app.config["JWT_SECRET_KEY"],
        expires_in=current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES", 3600),
    )
    app_logger.info("User logged in: %s", email)
    return True, "Login successful", {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]},
    }
