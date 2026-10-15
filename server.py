"""Thinking Pattern Memory MCP with Neon Better Auth and guest commons."""
import os

import jwt as pyjwt
import psycopg
from jwt import PyJWKClient
from mcp.server.fastmcp import Context, FastMCP

from auth import register_oauth_routes

DATABASE_URL = os.environ.get("DATABASE_URL")
NEON_AUTH_BASE_URL = os.environ.get("NEON_AUTH_BASE_URL", "").rstrip("/")
JWKS_URL = os.environ.get("NEON_AUTH_JWKS_URL") or (
    NEON_AUTH_BASE_URL + "/.well-known/jwks.json" if NEON_AUTH_BASE_URL else None
)

mcp = FastMCP(
    "my-first-mem",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS patterns (
    id SERIAL PRIMARY KEY,
    pattern TEXT NOT NULL,
    note TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured")
    conn = psycopg.connect(DATABASE_URL)
    with conn.cursor() as cur:
        cur.execute(SCHEMA)
    conn.commit()
    return conn


def current_identity(ctx: Context):
    """No bearer token means guest; invalid bearer token must raise."""
    request = getattr(ctx.request_context, "request", None)
    auth = request.headers.get("authorization", "") if request is not None else ""
    if not auth.lower().startswith("bearer "):
        return None, None
    token = auth.split(None, 1)[1]
    if token == "guest-no-shelf":
        return None, None
    if not JWKS_URL:
        raise RuntimeError("NEON_AUTH_BASE_URL is missing")
    signing_key = PyJWKClient(JWKS_URL).get_signing_key_from_jwt(token)
    claims = pyjwt.decode(
        token,
        signing_key.key,
        algorithms=["EdDSA", "ES256", "RS256"],
        options={"verify_aud": False},
    )
    return claims["sub"], claims.get("email")


@mcp.tool()
def user_status(ctx: Context) -> str:
    """Report whether the caller is a guest or a signed-in user."""
    user_id, email = current_identity(ctx)
    if user_id is None:
        return "guest — thinking patterns are in the shared commons."
    return f"user — signed in as {email or user_id}. Your thinking patterns are private."


@mcp.tool()
def record_pattern(pattern: str, ctx: Context, note: str = "") -> str:
    """Record a thinking pattern for the current user or guest commons."""
    user_id, _ = current_identity(ctx)
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO patterns (pattern, note, user_id) VALUES (%s, %s, %s) "
            "RETURNING id, recorded_at",
            (pattern, note or None, user_id),
        )
        pattern_id, ts = cur.fetchone()
        conn.commit()
    shelf = "your private memory" if user_id else "the guest commons"
    return f"Recorded thinking pattern #{pattern_id} at {ts.isoformat()} in {shelf}."


@mcp.tool()
def list_patterns(ctx: Context) -> str:
    """List the current user's patterns, oldest first."""
    user_id, _ = current_identity(ctx)
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, pattern, note, recorded_at FROM patterns "
            "WHERE user_id IS NOT DISTINCT FROM %s ORDER BY id",
            (user_id,),
        )
        rows = cur.fetchall()
    if not rows:
        return "No thinking patterns have been recorded on this shelf yet."
    lines = []
    for pattern_id, pattern, note, ts in rows:
        extra = f" — {note}" if note else ""
        lines.append(f'#{pattern_id} ({ts:%Y-%m-%d %H:%M}): "{pattern}"{extra}')
    return "\n".join(lines)


register_oauth_routes(mcp)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
