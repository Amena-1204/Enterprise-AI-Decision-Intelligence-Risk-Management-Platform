import re
from typing import Any, Dict, List, Optional, Tuple


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit"
    return True, ""


def validate_required_fields(data: Dict[str, Any], fields: List[str]) -> Optional[str]:
    """Return an error message if any required field is missing or empty."""
    for field in fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return f"Field '{field}' is required"
    return None


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Strip whitespace and truncate to max_length."""
    return str(value).strip()[:max_length]


def validate_positive_number(value: Any, field_name: str) -> Tuple[bool, str]:
    try:
        num = float(value)
        if num < 0:
            return False, f"'{field_name}' must be a non-negative number"
        return True, ""
    except (TypeError, ValueError):
        return False, f"'{field_name}' must be a valid number"
