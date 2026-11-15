from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from backend.app.database.connection import execute_query, execute_write


@dataclass
class User:
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    role: str = "viewer"
    is_active: bool = True
    created_at: Optional[datetime] = None

    @staticmethod
    def find_by_email(email: str) -> Optional[dict]:
        rows = execute_query("SELECT * FROM users WHERE email = %s LIMIT 1", (email,))
        return rows[0] if rows else None

    @staticmethod
    def find_by_id(user_id: int) -> Optional[dict]:
        rows = execute_query("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
        return rows[0] if rows else None

    @staticmethod
    def create(username: str, email: str, password_hash: str, role: str = "viewer") -> int:
        return execute_write(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (username, email, password_hash, role),
        )
