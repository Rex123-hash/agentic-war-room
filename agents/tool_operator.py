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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.data_store import add_action_log

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from tools.calendar_tool import create_calendar_event
from database.agent_logger import log_agent_event

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "stratify.db")
GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_HUDDLE_EMAIL = os.getenv("DEFAULT_HUDDLE_EMAIL", "amaank2405@gmail.com")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _log_action(tool: str, action: str, details: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO action_log (tool, action, details) VALUES (?, ?, ?)",
        (tool, action, details),
    )
    conn.commit()
    conn.close()


def reassign_task(task_id: int, new_assignee: str, reason: str) -> dict:
    conn = _connect()
    conn.execute("UPDATE tasks SET assignee = ? WHERE id = ?", (new_assignee, task_id))
    conn.commit()
    conn.close()
    details = f"Task {task_id} reassigned to {new_assignee}. Reason: {reason}"
    _log_action("TaskManager", "reassign_task", details)
    return {"status": "updated", "details": details}


def update_task_status(task_id: int, new_status: str, note: str) -> dict:
    conn = _connect()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    conn.close()
    details = f"Task {task_id} status changed to {new_status}. Note: {note}"
    _log_action("TaskManager", "update_task_status", details)
    return {"status": "updated", "details": details}


def record_notification(channel: str, message: str) -> dict:
    details = f"Notification recorded for {channel}: {message}"
    _log_action("Notification", "record_notification", details)
    return {"status": "recorded", "details": details}


def create_real_calendar_huddle(title: str, attendees: str, duration_minutes: int, description: str) -> dict:
    result = create_calendar_event(
        title=title,
        attendees=attendees,
        duration_minutes=duration_minutes,
        description=description,
    )

    event_link = result.get("event_link", "")
    valid_attendees = result.get("valid_attendees_count", 0)
    status = result.get("status", "unknown")
    reason = result.get("reason", "")

    details = (
        f"Calendar huddle result | "
        f"status={status} | "
        f"title={title} | "
        f"valid_attendees={valid_attendees} | "
        f"event_link={event_link} | "
        f"reason={reason}"
    )

    _log_action("GoogleCalendar", "create_real_calendar_huddle", details)
    return result


def get_action_log() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return {"actions": [dict(r) for r in rows]}


def _needs_huddle(instructions: str) -> bool:
    text = instructions.lower()
    keywords = ["emergency huddle", "calendar", "meeting", "urgent sync", "coordination", "huddle"]
    return any(word in text for word in keywords)


TOOL_OPERATOR_PROMPT = """
You are the Tool Operator.
Use tools to make real updates inside the system database.

You can:
- reassign tasks
- update task status
- record notifications
- create a real Google Calendar huddle
- inspect recent action logs

Rules:
- If a calendar tool returns status=success, report the event link.
- If a calendar tool returns status=skipped or error, report the exact reason and recommend manual scheduling.
- Do not say you are waiting for email addresses when DEFAULT_HUDDLE_EMAIL was already used.
"""


async def run_tool_operator(instructions: str) -> dict:
    print(f"[TOOL OPERATOR] Instructions: {instructions[:100]}...")
    log_agent_event("ToolOperatorAgent", "started", instructions[:500])
    preflight_notes = []

    if _needs_huddle(instructions):
        try:
            result = create_real_calendar_huddle(
                title="Stratify Emergency Huddle",
                attendees=DEFAULT_HUDDLE_EMAIL,
                duration_minutes=15,
                description="Auto-created by Stratify during critical project risk handling.",
            )
            preflight_notes.append(f"Calendar preflight result: {result}")
        except Exception as exc:
            _log_action("GoogleCalendar", "create_real_calendar_huddle_failed", f"error={exc}")
            preflight_notes.append(f"Calendar preflight failed: {exc}")

    agent = LlmAgent(
        name="ToolOperatorAgent",
        model=GEMINI_MODEL,
        instruction=TOOL_OPERATOR_PROMPT,
        tools=[
            FunctionTool(reassign_task),
            FunctionTool(update_task_status),
            FunctionTool(record_notification),
            FunctionTool(create_real_calendar_huddle),
            FunctionTool(get_action_log),
        ],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="agentic-stratify", session_service=session_service)
    session = await session_service.create_session(app_name="agentic-stratify", user_id="user_001")

    full_instructions = instructions
    if preflight_notes:
        full_instructions = instructions + "\n\n" + "\n".join(preflight_notes)

    message = types.Content(role="user", parts=[types.Part(text=full_instructions)])
    response_text = ""

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            print("[TOOL OPERATOR] Done")
            log_agent_event("ToolOperatorAgent", "completed", response_text[:500])

    return {"summary": response_text}


async def main():
    result = await run_tool_operator(
        "Reassign task 1 to Carol White, update task 1 status to In Progress, record a notification, and create a real Google Calendar emergency huddle."
    )
    print(result["summary"])


if __name__ == "__main__":
    asyncio.run(main())
