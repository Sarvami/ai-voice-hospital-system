"""Web Push helpers — uses VAPID keys from env or auto-generated file."""
import json
import os
import sqlite3
from pathlib import Path

VAPID_FILE = Path(__file__).parent / "data" / "vapid_keys.json"


def _load_or_create_vapid():
    pub = os.getenv("VAPID_PUBLIC_KEY")
    priv = os.getenv("VAPID_PRIVATE_KEY")
    if pub and priv:
        return {"publicKey": pub, "privateKey": priv}
    if VAPID_FILE.exists():
        return json.loads(VAPID_FILE.read_text(encoding="utf-8"))
    try:
        from py_vapid import Vapid
        v = Vapid()
        v.generate_keys()
        pub = v.public_key
        priv = v.private_key
        if callable(getattr(pub, "decode", None)):
            pub = pub.decode("utf-8")
        if callable(getattr(priv, "decode", None)):
            priv = priv.decode("utf-8")
        keys = {"publicKey": str(pub), "privateKey": str(priv)}
        VAPID_FILE.parent.mkdir(parents=True, exist_ok=True)
        VAPID_FILE.write_text(json.dumps(keys), encoding="utf-8")
        return keys
    except Exception as e:
        print("VAPID key generation skipped:", e)
        return None


def get_vapid_public_key() -> str | None:
    keys = _load_or_create_vapid()
    return keys["publicKey"] if keys else None


def save_subscription(conn: sqlite3.Connection, patient_id: int, subscription: dict):
    endpoint = subscription.get("endpoint", "")
    if not endpoint:
        return
    conn.execute(
        """INSERT OR REPLACE INTO push_subscriptions
           (patient_id, endpoint, subscription_json)
           VALUES (?, ?, ?)""",
        (patient_id, endpoint, json.dumps(subscription)),
    )
    conn.commit()


def send_push_to_all(conn: sqlite3.Connection, title: str, body: str):
    """Best-effort push to all subscribed patients."""
    keys = _load_or_create_vapid()
    if not keys:
        return 0
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        print("pywebpush not installed — skipping browser push")
        return 0

    rows = conn.execute("SELECT subscription_json FROM push_subscriptions").fetchall()
    sent = 0
    payload = json.dumps({"title": title, "body": body})
    for row in rows:
        try:
            sub = json.loads(row["subscription_json"])
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=keys["privateKey"],
                vapid_claims={"sub": "mailto:admin@swasthseva.local"},
            )
            sent += 1
        except WebPushException as e:
            print("Push failed:", e)
        except Exception as e:
            print("Push error:", e)
    return sent
