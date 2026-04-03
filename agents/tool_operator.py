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
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "warroom.db")
GEMINI_MODEL = "gemini-2.5-flash"


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
    conn.execute(
        "UPDATE tasks SET assignee = ? WHERE id = ?",
        (new_assignee, task_id),
    )
    conn.commit()
    conn.close()
    details = f"Task {task_id} reassigned to {new_assignee}. Reason: {reason}"
    _log_action("TaskManager", "reassign_task", details)
    return {"status": "updated", "details": details}


def update_task_status(task_id: int, new_status: str, note: str) -> dict:
    conn = _connect()
    conn.execute(
        "UPDATE tasks SET status = ? WHERE id = ?",
        (new_status, task_id),
    )
    conn.commit()
    conn.close()
    details = f"Task {task_id} status changed to {new_status}. Note: {note}"
    _log_action("TaskManager", "update_task_status", details)
    return {"status": "updated", "details": details}


def record_notification(channel: str, message: str) -> dict:
    details = f"Notification recorded for {channel}: {message}"
    _log_action("Notification", "record_notification", details)
    return {"status": "recorded", "details": details}


def record_meeting(title: str, attendees: str, duration_minutes: int, description: str) -> dict:
    details = f"Meeting recorded: {title} | Attendees: {attendees} | Duration: {duration_minutes} | Description: {description}"
    _log_action("Calendar", "record_meeting", details)
    return {"status": "recorded", "details": details}


def get_action_log() -> dict:
    conn = _connect()
    rows = conn.execute("SELECT * FROM action_log ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    return {"actions": [dict(r) for r in rows]}


TOOL_OPERATOR_PROMPT = """
You are the Tool Operator.
Use tools to make real updates inside the system database.
Do not claim that Slack, Jira, or Calendar were actually called externally.
If needed, record notifications and meetings as internal operational actions.
"""


async def run_tool_operator(instructions: str) -> dict:
    print(f"[TOOL OPERATOR] Instructions: {instructions[:80]}...")

    agent = LlmAgent(
        name="ToolOperatorAgent",
        model=GEMINI_MODEL,
        instruction=TOOL_OPERATOR_PROMPT,
        tools=[
            FunctionTool(reassign_task),
            FunctionTool(update_task_status),
            FunctionTool(record_notification),
            FunctionTool(record_meeting),
            FunctionTool(get_action_log),
        ],
    )

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="agentic-war-room", session_service=session_service)
    session = await session_service.create_session(app_name="agentic-war-room", user_id="user_001")

    message = types.Content(role="user", parts=[types.Part(text=instructions)])
    response_text = ""

    async for event in runner.run_async(
        user_id="user_001",
        session_id=session.id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
            print("[TOOL OPERATOR] Done")

    return {"summary": response_text}


async def main():
    result = await run_tool_operator(
        "Reassign task 1 to Bob Johnson, update task 1 status to In Progress, record a notification to engineering-critical, and record an emergency huddle for Bob Johnson and Project Manager."
    )
    print(result["summary"])


if __name__ == "__main__":
    asyncio.run(main())