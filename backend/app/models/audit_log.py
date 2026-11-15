from __future__ import annotations
import json
from typing import Any, Dict, Optional

from backend.app.database.connection import execute_write


class AuditLog:
    @staticmethod
    def log(
        action: str,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        execute_write(
            """INSERT INTO audit_logs
               (user_id, action, resource, resource_id, ip_address, details)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, action, resource, resource_id, ip_address,
             json.dumps(details) if details else None),
        )
