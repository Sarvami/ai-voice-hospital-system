import asyncio
import sqlite3
import datetime
import secrets
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
from database import get_db_connection

class ConnectionManager:
    def __init__(self):
        # Maps (user_type, user_id) -> WebSocket
        self.active_connections: Dict[tuple[str, int], WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_type: str, user_id: int):
        await websocket.accept()
        self.active_connections[(user_type, user_id)] = websocket

    def disconnect(self, user_type: str, user_id: int):
        if (user_type, user_id) in self.active_connections:
            del self.active_connections[(user_type, user_id)]

    async def send_personal_message(self, message: dict, user_type: str, user_id: int):
        websocket = self.active_connections.get((user_type, user_id))
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to {user_type}_{user_id}: {e}")
                self.disconnect(user_type, user_id)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections.values()):
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def ping_clients(self):
        """Background task to ping active clients to keep connection alive."""
        while True:
            await asyncio.sleep(30)
            for key, websocket in list(self.active_connections.items()):
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    self.disconnect(key[0], key[1])

manager = ConnectionManager()


def notify_personal(message: dict, user_type: str, user_id: int):
    """Schedule a WebSocket notification when a loop is running; no-op in sync contexts."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.send_personal_message(message, user_type, user_id))
    except RuntimeError:
        pass


def generate_ws_token(user_type: str, user_id: int) -> str:
    """Generate and store a token for WS auth."""
    token = secrets.token_urlsafe(32)
    # Expiry 1 hour from now
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO ws_tokens (token, user_type, user_id, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_type, user_id, expires_at)
        )
        conn.commit()
    finally:
        conn.close()
    return token

def validate_ws_token(token: str) -> tuple[str, int]:
    """Validate token and return (user_type, user_id) or (None, None)."""
    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT user_type, user_id, expires_at FROM ws_tokens WHERE token = ?",
            (token,)
        ).fetchone()
        
        if row:
            # Check expiry
            expires_at = datetime.datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S.%f")
            if datetime.datetime.utcnow() < expires_at:
                return row["user_type"], row["user_id"]
            else:
                # Expired token cleanup
                conn.execute("DELETE FROM ws_tokens WHERE token = ?", (token,))
                conn.commit()
    finally:
        conn.close()
    
    return None, None

def revoke_ws_token(token: str):
    """Revoke a token (e.g. on logout)."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT user_type, user_id FROM ws_tokens WHERE token = ?", (token,)).fetchone()
        if row:
            # Drop the websocket connection immediately if exists
            manager.disconnect(row["user_type"], row["user_id"])
            
        conn.execute("DELETE FROM ws_tokens WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
