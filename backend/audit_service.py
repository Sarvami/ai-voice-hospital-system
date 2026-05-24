"""Central audit logging for admin-tracked changes."""
import json
import sqlite3
from typing import Any, Optional


def log_audit(
    conn: sqlite3.Connection,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
):
    conn.execute(
        """INSERT INTO audit_log (actor, action, entity_type, entity_id, details)
           VALUES (?, ?, ?, ?, ?)""",
        (actor, action, entity_type, entity_id, json.dumps(details or {})),
    )
    conn.commit()


def get_audit_logs(conn: sqlite3.Connection, limit: int = 200):
    rows = conn.execute(
        """SELECT id, actor, action, entity_type, entity_id, details, created_at
           FROM audit_log ORDER BY created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["details"] = json.loads(d.get("details") or "{}")
        except json.JSONDecodeError:
            d["details"] = {}
        result.append(d)
    return result
