from __future__ import annotations

import json
from typing import Any, Dict, Optional

from backend.app.database.connection import execute_write
from backend.app.utils.logger import app_logger


def write_audit_log(
    action: str,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist an audit log entry. Silently swallows DB errors so it never
    breaks the main request flow."""
    try:
        execute_write(
            """INSERT INTO audit_logs
               (user_id, action, resource, resource_id, ip_address, details)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                user_id,
                action,
                resource,
                str(resource_id) if resource_id is not None else None,
                ip_address,
                json.dumps(details) if details else None,
            ),
        )
    except Exception as exc:
        app_logger.warning("audit_log write failed: %s", exc)
