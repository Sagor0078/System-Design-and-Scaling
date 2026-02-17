"""Shared PostgreSQL helpers used by every demo script."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row



def pg_conn(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "module2_db",
    user: str = "postgres",
    password: str = "example",
    autocommit: bool = False,
):
    """Return a psycopg (v3) connection."""
    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        autocommit=autocommit,
    )
    return conn


def pg_primary(autocommit: bool = False):
    """Connect to the PRIMARY on port 5432."""
    return pg_conn(port=5432, autocommit=autocommit)


def pg_replica(autocommit: bool = False):
    """Connect to the REPLICA on port 5433 (read-only)."""
    return pg_conn(port=5433, autocommit=autocommit)


def pg_shard(shard_id: int, autocommit: bool = False):
    """Connect to the shard (0 → primary 5432, 1 → shard-2 5442)."""
    port = 5432 if shard_id == 0 else 5442
    return pg_conn(port=port, autocommit=autocommit)



USERS_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    region TEXT NOT NULL
);
"""


def ensure_schema(conn):
    """Create the users table if it doesn't exist."""
    with conn.cursor() as cur:
        cur.execute(USERS_DDL)
    conn.commit()


def insert_user(conn, name: str, region: str) -> int:
    """Insert a row and return its id."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (name, region) VALUES (%s, %s) RETURNING id",
            (name, region),
        )
        row = cur.fetchone()
        uid = row[0]
    conn.commit()
    return uid


def fetch_all_users(conn) -> list[dict]:
    """Return every row as a dict."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT id, name, region FROM users ORDER BY id")
        return cur.fetchall()
