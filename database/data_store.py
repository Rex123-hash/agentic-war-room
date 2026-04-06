import os
import sys
import sqlite3
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.firestore_db import (
    is_firestore_enabled,
    upsert_document,
    add_document,
    list_documents,
    get_document,
    delete_document,
)
from database.db_setup import DB_PATH


def get_sqlite_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ----------------------------
# TASKS
# ----------------------------
def get_all_tasks() -> List[Dict[str, Any]]:
    if is_firestore_enabled():
        docs = list_documents("tasks")
        return sorted(
            docs,
            key=lambda x: (
                {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}.get(x.get("priority", "Low"), 5),
                str(x.get("id", "")),
            ),
        )

    conn = get_sqlite_connection()
    rows = conn.execute(
        """
        SELECT id, title, assignee, status, priority, deadline, description, created_at
        FROM tasks
        ORDER BY
            CASE priority
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            id
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_task(title: str, assignee: str, status: str, priority: str, deadline: str, description: str) -> str:
    if is_firestore_enabled():
        return add_document(
            "tasks",
            {
                "title": title,
                "assignee": assignee,
                "status": status,
                "priority": priority,
                "deadline": deadline,
                "description": description,
                "created_at": now_iso(),
            },
        )

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO tasks (title, assignee, status, priority, deadline, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, assignee, status, priority, deadline, description),
    )
    conn.commit()
    task_id = str(cur.lastrowid)
    conn.close()
    return task_id


def update_task(task_id: str, assignee: str, status: str) -> None:
    if is_firestore_enabled():
        upsert_document(
            "tasks",
            task_id,
            {
                "assignee": assignee,
                "status": status,
                "updated_at": now_iso(),
            },
        )
        return

    conn = get_sqlite_connection()
    conn.execute(
        "UPDATE tasks SET assignee = ?, status = ? WHERE id = ?",
        (assignee, status, task_id),
    )
    conn.commit()
    conn.close()


def delete_task(task_id: str) -> None:
    if is_firestore_enabled():
        delete_document("tasks", task_id)
        return

    conn = get_sqlite_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# ----------------------------
# TEAM MEMBERS
# ----------------------------
def get_all_team_members() -> List[Dict[str, Any]]:
    if is_firestore_enabled():
        docs = list_documents("team_members")
        return sorted(docs, key=lambda x: str(x.get("id", "")))

    conn = get_sqlite_connection()
    rows = conn.execute(
        """
        SELECT id, name, role, email, skills, available
        FROM team_members
        ORDER BY id
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_team_member(name: str, role: str, email: str, skills: str, available: bool) -> str:
    if is_firestore_enabled():
        return add_document(
            "team_members",
            {
                "name": name,
                "role": role,
                "email": email,
                "skills": skills,
                "available": available,
                "created_at": now_iso(),
            },
        )

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO team_members (name, role, email, skills, available)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, role, email, skills, 1 if available else 0),
    )
    conn.commit()
    member_id = str(cur.lastrowid)
    conn.close()
    return member_id


def update_team_member_availability(member_id: str, available: bool) -> None:
    if is_firestore_enabled():
        upsert_document(
            "team_members",
            member_id,
            {
                "available": available,
                "updated_at": now_iso(),
            },
        )
        return

    conn = get_sqlite_connection()
    conn.execute(
        "UPDATE team_members SET available = ? WHERE id = ?",
        (1 if available else 0, member_id),
    )
    conn.commit()
    conn.close()


def delete_team_member(member_id: str) -> None:
    if is_firestore_enabled():
        delete_document("team_members", member_id)
        return

    conn = get_sqlite_connection()
    conn.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()


# ----------------------------
# ACTION LOG
# ----------------------------
def get_action_logs(limit: int = 20) -> List[Dict[str, Any]]:
    if is_firestore_enabled():
        docs = list_documents("action_log")
        docs = sorted(docs, key=lambda x: x.get("timestamp", ""), reverse=True)
        return docs[:limit]

    conn = get_sqlite_connection()
    rows = conn.execute(
        """
        SELECT id, tool, action, details, timestamp
        FROM action_log
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_action_log(tool: str, action: str, details: str) -> str:
    if is_firestore_enabled():
        return add_document(
            "action_log",
            {
                "tool": tool,
                "action": action,
                "details": details,
                "timestamp": now_iso(),
            },
        )

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO action_log (tool, action, details)
        VALUES (?, ?, ?)
        """,
        (tool, action, details),
    )
    conn.commit()
    log_id = str(cur.lastrowid)
    conn.close()
    return log_id