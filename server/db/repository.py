"""Database repository for persisting request state and audit trail.

Requires env var: DATABASE_URL (PostgreSQL connection string).
"""

import os
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS requests (
    request_id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    review_verdict TEXT,
    approval_id TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS approval_audit (
    id SERIAL PRIMARY KEY,
    approval_id TEXT NOT NULL REFERENCES requests(approval_id),
    request_id TEXT NOT NULL REFERENCES requests(request_id),
    decision TEXT NOT NULL,
    reviewer TEXT,
    reason TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_requests_approval_id
    ON requests(approval_id) WHERE approval_id IS NOT NULL;
"""


@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migrations() -> None:
    """Create the ``requests`` and ``approval_audit`` tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)


def upsert_request(
    request_id: str,
    query: str,
    status: str,
    result: str | None = None,
    review_verdict: str | None = None,
    approval_id: str | None = None,
    created_at: datetime | None = None,
) -> None:
    """Insert a new request or update its status/result on conflict."""
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO requests
                    (request_id, query, status, result, review_verdict,
                     approval_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (request_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    result = EXCLUDED.result,
                    review_verdict = EXCLUDED.review_verdict
                """,
                (
                    request_id,
                    query,
                    status,
                    result,
                    review_verdict,
                    approval_id,
                    created_at,
                ),
            )


def get_request_by_id(request_id: str) -> dict | None:
    """Fetch a single request row as a dict, or *None* if not found."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM requests WHERE request_id = %s",
                (request_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def get_request_id_by_approval(approval_id: str) -> str | None:
    """Resolve an approval_id to its parent request_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT request_id FROM requests WHERE approval_id = %s",
                (approval_id,),
            )
            row = cur.fetchone()
            return row[0] if row else None


def insert_audit_record(
    approval_id: str,
    request_id: str,
    decision: str,
    reviewer: str | None = None,
    reason: str | None = None,
) -> None:
    """Record an approval decision in the audit trail."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO approval_audit
                    (approval_id, request_id, decision, reviewer, reason)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (approval_id, request_id, decision, reviewer, reason),
            )
