import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Tuple

import mysql.connector
from mysql.connector import pooling

from backend.app.utils.logger import app_logger

_pool: Optional[pooling.MySQLConnectionPool] = None


def init_pool(config) -> None:
    """Initialize the MySQL connection pool from app config."""
    global _pool
    pool_config = {
        "pool_name": "enterprise_ai_pool",
        "pool_size": 10,
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "database": config.DB_NAME,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
        "time_zone": "+00:00",
    }
    _pool = pooling.MySQLConnectionPool(**pool_config)
    app_logger.info("MySQL connection pool initialized (host=%s db=%s)", config.DB_HOST, config.DB_NAME)


@contextmanager
def get_db() -> Generator[mysql.connector.MySQLConnection, None, None]:
    """Context manager that yields a pooled connection and handles commit/rollback."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    conn = _pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(
    sql: str,
    params: Optional[Tuple] = None,
    fetch: bool = True,
) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return rows as list of dicts."""
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        if fetch:
            return cursor.fetchall()
        return []


def execute_write(
    sql: str,
    params: Optional[Tuple] = None,
) -> int:
    """Execute an INSERT/UPDATE/DELETE and return lastrowid or rowcount."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        return cursor.lastrowid or cursor.rowcount


def execute_many(sql: str, params_list: List[Tuple]) -> int:
    """Execute a batch INSERT/UPDATE."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        return cursor.rowcount
