import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "warroom.db")


def save_message(session_id: str, role: str, message: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, message) VALUES (?, ?, ?)",
        (session_id, role, message),
    )
    conn.commit()
    conn.close()


def get_recent_messages(session_id: str, limit: int = 8) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT role, message, created_at
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (session_id, limit),
    ).fetchall()
    conn.close()

    messages = [dict(r) for r in rows]
    messages.reverse()
    return messages


def clear_session_messages(session_id: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
