import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "warroom.db")


def log_agent_event(agent_name: str, stage: str, message: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO agent_runs (agent_name, stage, message) VALUES (?, ?, ?)",
        (agent_name, stage, message),
    )
    conn.commit()
    conn.close()


def clear_agent_runs() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM agent_runs")
    conn.commit()
    conn.close()