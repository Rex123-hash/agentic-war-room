import os
import sys
import sqlite3
from datetime import datetime, UTC

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.data_store import add_action_log
from database.db_setup import DB_PATH


def log_agent_event(agent_name: str, stage: str, message: str) -> None:
    timestamp = datetime.now(UTC).isoformat()

    # SQLite backup
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO agent_runs (agent_name, stage, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (agent_name, stage, message, timestamp),
    )
    conn.commit()
    conn.close()

    # Firestore action log
    try:
        add_action_log(
            tool="AgentLogger",
            action=f"{agent_name}:{stage}",
            details=message,
        )
    except Exception:
        pass


def clear_agent_runs() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM agent_runs")
    conn.commit()
    conn.close()