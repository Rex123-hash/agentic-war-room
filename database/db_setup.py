import os
import sqlite3
from datetime import datetime, UTC

from database.firestore_db import is_firestore_enabled, upsert_document

DB_PATH = os.path.join(os.path.dirname(__file__), "warroom.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def setup_sqlite_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee TEXT,
            status TEXT DEFAULT 'Open',
            priority TEXT DEFAULT 'Medium',
            deadline TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT,
            email TEXT,
            skills TEXT,
            available INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            title TEXT,
            content TEXT,
            date TEXT
        );

        CREATE TABLE IF NOT EXISTS action_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool TEXT,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            stage TEXT NOT NULL,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    conn.commit()
    conn.close()


def setup_firestore_collections():
    if not is_firestore_enabled():
        print("Firestore is not enabled. Skipping Firestore setup.")
        return

    now = datetime.now(UTC).isoformat()

    bootstrap_docs = {
        "system_meta": {
            "app": "Project War-Room",
            "status": "initialized",
            "initialized_at": now,
        }
    }

    for doc_id, payload in bootstrap_docs.items():
        upsert_document("system_meta", doc_id, payload)

    print("Firestore bootstrap complete.")


def setup_database():
    setup_sqlite_database()
    print("SQLite setup complete.")

    if is_firestore_enabled():
        setup_firestore_collections()


if __name__ == "__main__":
    setup_database()
