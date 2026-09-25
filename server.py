"""my-first-mem — a memory for thinking patterns.

This server lets a model record thinking patterns that I notice
and retrieve them later, even across different conversations.
"""

import os
from mcp.server.fastmcp import FastMCP
import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL")

mcp = FastMCP(
    "my-first-mem",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns (
    id          SERIAL PRIMARY KEY,
    pattern     TEXT NOT NULL,
    note        TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def db():
    """Connect to the database."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Create a database at neon.tech "
            "and set the connection string as an environment variable."
        )

    conn = psycopg.connect(DATABASE_URL)

    with conn.cursor() as cur:
        cur.execute(SCHEMA)

    conn.commit()
    return conn


@mcp.tool()
def record_pattern(pattern: str, note: str = "") -> str:
    """Save a thinking pattern that I want to remember."""

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO patterns (pattern, note) VALUES (%s, %s) "
            "RETURNING id, recorded_at",
            (pattern, note or None),
        )

        pattern_id, ts = cur.fetchone()
        conn.commit()

    return f"Recorded thinking pattern #{pattern_id} at {ts.isoformat()}."


@mcp.tool()
def list_patterns() -> str:
    """List all thinking patterns in memory, oldest first."""

    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, pattern, note, recorded_at "
            "FROM patterns ORDER BY id"
        )

        rows = cur.fetchall()

    if not rows:
        return "No thinking patterns have been recorded yet."

    lines = []

    for pattern_id, pattern, note, ts in rows:
        extra = f" — {note}" if note else ""
        lines.append(
            f'#{pattern_id} ({ts:%Y-%m-%d %H:%M}): "{pattern}"{extra}'
        )

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
