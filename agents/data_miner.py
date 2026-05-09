import os
import sys
import sqlite3
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from database.data_store import get_all_tasks, get_all_team_members

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database.agent_logger import log_agent_event

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "stratify.db")
GEMINI_MODEL = "gemini-2.5-flash-lite"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_tasks() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    conn.close()
    return {"tasks": [dict(r) for r in rows]}


def get_critical_tasks() -> dict:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM tasks
        WHERE priority IN ('Critical', 'High') AND status != 'Closed'
        ORDER BY deadline ASC
        """
    ).fetchall()
    conn.close()
    return {"critical_tasks": [dict(r) for r in rows]}


def get_available_developers() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM team_members WHERE available = 1").fetchall()
    conn.close()
    return {"available_developers": [dict(r) for r in rows]}


def get_team_status() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM team_members").fetchall()
    conn.close()
    return {"team": [dict(r) for r in rows]}


def get_blocked_tasks() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM tasks WHERE status = 'Blocked'").fetchall()
    conn.close()
    return {"blocked_tasks": [dict(r) for r in rows]}


DATA_MINER_PROMPT = """
You are the Data Miner sub-agent.
You must always use tools to fetch real project data from the database.
Return concise structured findings for the Commander.
"""


async def run_data_miner(goal: str) -> str:
    log_agent_event("DataMinerAgent", "started", goal)

    raw_tasks = get_all_tasks()
    raw_team_members = get_all_team_members()

    tasks = [item for item in raw_tasks if isinstance(item, dict)]
    team_members = [item for item in raw_team_members if isinstance(item, dict)]

    open_tasks = [t for t in tasks if t.get("status") != "Closed"]
    blocked_tasks = [t for t in tasks if t.get("status") == "Blocked"]
    critical_tasks = [
        t for t in tasks
        if t.get("priority") == "Critical" and t.get("status") != "Closed"
    ]
    available_members = [
        m for m in team_members
        if m.get("available") in [True, 1, "Available"]
    ]
    unavailable_members = [
        m for m in team_members
        if m.get("available") not in [True, 1, "Available"]
    ]

    task_snapshot = []
    for task in open_tasks[:5]:
        task_snapshot.append(
            f"- {task.get('title', 'Untitled')} | "
            f"Assignee: {task.get('assignee', 'Unassigned')} | "
            f"Status: {task.get('status', 'Unknown')} | "
            f"Priority: {task.get('priority', 'Unknown')} | "
            f"Deadline: {task.get('deadline', 'N/A')}"
        )

    team_snapshot = []
    for member in team_members[:5]:
        availability = "Available" if member.get("available") in [True, 1, "Available"] else "Unavailable"
        team_snapshot.append(
            f"- {member.get('name', 'Unknown')} | "
            f"Role: {member.get('role', 'N/A')} | "
            f"Availability: {availability}"
        )

    summary = f"""
Open Tasks: {len(open_tasks)}
Blocked Tasks: {len(blocked_tasks)}
Critical Open Tasks: {len(critical_tasks)}
Available Team Members: {len(available_members)}
Unavailable Team Members: {len(unavailable_members)}

Task Snapshot:
{chr(10).join(task_snapshot) if task_snapshot else "- No open tasks found"}

Team Snapshot:
{chr(10).join(team_snapshot) if team_snapshot else "- No team members found"}
""".strip()

    log_agent_event("DataMinerAgent", "completed", "Project data analyzed")
    return summary

async def main():
    result = await run_data_miner("What are the critical tasks, blocked tasks, and available developers right now?")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())